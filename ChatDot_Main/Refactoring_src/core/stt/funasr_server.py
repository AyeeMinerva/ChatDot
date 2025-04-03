"""
FunASR WebSocket服务器
基于原始的funasr_wss_server.py改造，内置到STT模块中
"""
import asyncio
import json
import websockets
import time
import ssl
import os
import sys
import threading
from typing import Set, Dict, Any
from global_managers.logger_manager import LoggerManager

class FunASRServer:
    """FunASR服务器类"""
    
    def __init__(self):
        """初始化FunASR服务器"""
        self.host = "localhost"
        self.port = 10095
        self.device = "cuda"
        self.ngpu = 1
        self.ncpu = 4
        self.models = {}
        self.server_task = None
        self.server_thread = None
        self.is_running = False
        self.websocket_users = set()
        self.logger = LoggerManager().get_logger()
        
        # 模型实例
        self.model_asr = None
        self.model_asr_streaming = None
        self.model_vad = None
        self.model_punc = None
        
    def set_config(self, host="localhost", port=10095, device="cuda", 
                   ngpu=1, ncpu=4, models=None):
        """设置服务器配置"""
        self.host = host
        self.port = port
        self.device = device
        self.ngpu = ngpu
        self.ncpu = ncpu
        
        # 默认模型配置
        if models is None:
            self.models = {
                "asr_model": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                "asr_model_revision": "v2.0.4",
                "asr_model_online": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online",
                "asr_model_online_revision": "v2.0.4",
                "vad_model": "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
                "vad_model_revision": "v2.0.4",
                "punc_model": "iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727",
                "punc_model_revision": "v2.0.4"
            }
        else:
            self.models = models
            
    def load_models(self):
        """加载FunASR模型"""
        self.logger.info("正在加载FunASR模型...")
        
        try:
            from funasr import AutoModel
            
            # 加载ASR模型
            self.model_asr = AutoModel(
                model=self.models.get("asr_model"),
                model_revision=self.models.get("asr_model_revision"),
                ngpu=self.ngpu,
                ncpu=self.ncpu,
                device=self.device,
                disable_pbar=True,
                disable_log=True,
            )
            
            # 加载在线ASR模型
            self.model_asr_streaming = AutoModel(
                model=self.models.get("asr_model_online"),
                model_revision=self.models.get("asr_model_online_revision"),
                ngpu=self.ngpu,
                ncpu=self.ncpu,
                device=self.device,
                disable_pbar=True,
                disable_log=True,
            )
            
            # 加载VAD模型
            self.model_vad = AutoModel(
                model=self.models.get("vad_model"),
                model_revision=self.models.get("vad_model_revision"),
                ngpu=self.ngpu,
                ncpu=self.ncpu,
                device=self.device,
                disable_pbar=True,
                disable_log=True,
            )
            
            # 加载标点模型
            if self.models.get("punc_model"):
                self.model_punc = AutoModel(
                    model=self.models.get("punc_model"),
                    model_revision=self.models.get("punc_model_revision"),
                    ngpu=self.ngpu,
                    ncpu=self.ncpu,
                    device=self.device,
                    disable_pbar=True,
                    disable_log=True,
                )
            else:
                self.model_punc = None
                
            self.logger.info("FunASR模型加载完成")
            return True
            
        except ImportError:
            self.logger.error("未找到FunASR库，请安装: pip install funasr")
            return False
        except Exception as e:
            self.logger.error(f"加载FunASR模型失败: {e}")
            return False

    async def async_vad(self, websocket, audio_in):
        """语音活动检测"""
        segments_result = self.model_vad.generate(input=audio_in, **websocket.status_dict_vad)[0]["value"]
        
        speech_start = -1
        speech_end = -1
        
        if len(segments_result) == 0 or len(segments_result) > 1:
            return speech_start, speech_end
        if segments_result[0][0] != -1:
            speech_start = segments_result[0][0]
        if segments_result[0][1] != -1:
            speech_end = segments_result[0][1]
        return speech_start, speech_end

    async def async_asr(self, websocket, audio_in):
        """离线ASR处理"""
        if len(audio_in) > 0:
            rec_result = self.model_asr.generate(input=audio_in, **websocket.status_dict_asr)[0]
            
            if self.model_punc is not None and len(rec_result["text"]) > 0:
                rec_result = self.model_punc.generate(
                    input=rec_result["text"], **websocket.status_dict_punc
                )[0]
                
            if len(rec_result["text"]) > 0:
                mode = "2pass-offline" if "2pass" in websocket.mode else websocket.mode
                message = json.dumps(
                    {
                        "mode": mode,
                        "text": rec_result["text"],
                        "wav_name": websocket.wav_name,
                        "is_final": websocket.is_speaking,
                    }
                )
                await websocket.send(message)
        else:
            mode = "2pass-offline" if "2pass" in websocket.mode else websocket.mode
            message = json.dumps(
                {
                    "mode": mode,
                    "text": "",
                    "wav_name": websocket.wav_name,
                    "is_final": websocket.is_speaking,
                }
            )
            await websocket.send(message)

    async def async_asr_online(self, websocket, audio_in):
        """在线ASR处理"""
        if len(audio_in) > 0:
            rec_result = self.model_asr_streaming.generate(
                input=audio_in, **websocket.status_dict_asr_online
            )[0]
            
            if websocket.mode == "2pass" and websocket.status_dict_asr_online.get("is_final", False):
                return
                
            if len(rec_result["text"]):
                mode = "2pass-online" if "2pass" in websocket.mode else websocket.mode
                message = json.dumps(
                    {
                        "mode": mode,
                        "text": rec_result["text"],
                        "wav_name": websocket.wav_name,
                        "is_final": websocket.is_speaking,
                    }
                )
                await websocket.send(message)

    async def ws_reset(self, websocket):
        """重置WebSocket连接"""
        self.logger.debug(f"重置WebSocket连接，当前连接数: {len(self.websocket_users)}")
        
        websocket.status_dict_asr_online["cache"] = {}
        websocket.status_dict_asr_online["is_final"] = True
        websocket.status_dict_vad["cache"] = {}
        websocket.status_dict_vad["is_final"] = True
        websocket.status_dict_punc["cache"] = {}
        
        await websocket.close()

    async def handle_websocket(self, websocket, path=None):
        """处理WebSocket连接"""
        frames = []
        frames_asr = []
        frames_asr_online = []
        
        # 添加到用户集合
        self.websocket_users.add(websocket)
        
        # 初始化连接状态
        websocket.status_dict_asr = {}
        websocket.status_dict_asr_online = {"cache": {}, "is_final": False}
        websocket.status_dict_vad = {"cache": {}, "is_final": False}
        websocket.status_dict_punc = {"cache": {}}
        websocket.chunk_interval = 10
        websocket.vad_pre_idx = 0
        websocket.wav_name = "microphone"
        websocket.mode = "2pass"
        websocket.is_speaking = True
        
        speech_start = False
        speech_end_i = -1
        
        self.logger.debug("新WebSocket连接")
        
        try:
            async for message in websocket:
                # 处理字符串消息（配置消息）
                if isinstance(message, str):
                    config = json.loads(message)
                    
                    if "is_speaking" in config:
                        websocket.is_speaking = config["is_speaking"]
                        websocket.status_dict_asr_online["is_final"] = not websocket.is_speaking
                    if "chunk_interval" in config:
                        websocket.chunk_interval = config["chunk_interval"]
                    if "wav_name" in config:
                        websocket.wav_name = config["wav_name"]
                    if "chunk_size" in config:
                        chunk_size = config["chunk_size"]
                        if isinstance(chunk_size, str):
                            chunk_size = chunk_size.split(",")
                        websocket.status_dict_asr_online["chunk_size"] = [int(x) for x in chunk_size]
                    if "encoder_chunk_look_back" in config:
                        websocket.status_dict_asr_online["encoder_chunk_look_back"] = config["encoder_chunk_look_back"]
                    if "decoder_chunk_look_back" in config:
                        websocket.status_dict_asr_online["decoder_chunk_look_back"] = config["decoder_chunk_look_back"]
                    if "hotwords" in config:
                        websocket.status_dict_asr["hotword"] = config["hotwords"]
                    if "mode" in config:
                        websocket.mode = config["mode"]
                
                # 设置VAD分块大小
                websocket.status_dict_vad["chunk_size"] = int(
                    websocket.status_dict_asr_online["chunk_size"][1] * 60 / websocket.chunk_interval
                )
                
                # 处理音频数据
                if len(frames_asr_online) > 0 or len(frames_asr) >= 0 or not isinstance(message, str):
                    if not isinstance(message, str):
                        frames.append(message)
                        duration_ms = len(message) // 32
                        websocket.vad_pre_idx += duration_ms
                        
                        # ASR在线处理
                        frames_asr_online.append(message)
                        websocket.status_dict_asr_online["is_final"] = speech_end_i != -1
                        if (len(frames_asr_online) % websocket.chunk_interval == 0 or 
                            websocket.status_dict_asr_online["is_final"]):
                            if websocket.mode == "2pass" or websocket.mode == "online":
                                audio_in = b"".join(frames_asr_online)
                                try:
                                    await self.async_asr_online(websocket, audio_in)
                                except Exception as e:
                                    self.logger.error(f"在线ASR处理错误: {e}")
                            frames_asr_online = []
                        
                        # 如果检测到语音开始，就累积帧
                        if speech_start:
                            frames_asr.append(message)
                        
                        # VAD处理
                        try:
                            speech_start_i, speech_end_i = await self.async_vad(websocket, message)
                        except Exception as e:
                            self.logger.error(f"VAD处理错误: {e}")
                        
                        # 如果检测到语音开始
                        if speech_start_i != -1:
                            speech_start = True
                            beg_bias = (websocket.vad_pre_idx - speech_start_i) // duration_ms
                            frames_pre = frames[-min(beg_bias, len(frames)):]
                            frames_asr = []
                            frames_asr.extend(frames_pre)
                    
                    # 如果检测到语音结束或用户停止说话
                    if speech_end_i != -1 or not websocket.is_speaking:
                        if websocket.mode == "2pass" or websocket.mode == "offline":
                            audio_in = b"".join(frames_asr)
                            try:
                                await self.async_asr(websocket, audio_in)
                            except Exception as e:
                                self.logger.error(f"离线ASR处理错误: {e}")
                        
                        # 重置状态
                        frames_asr = []
                        speech_start = False
                        frames_asr_online = []
                        websocket.status_dict_asr_online["cache"] = {}
                        
                        if not websocket.is_speaking:
                            websocket.vad_pre_idx = 0
                            frames = []
                            websocket.status_dict_vad["cache"] = {}
                        else:
                            frames = frames[-20:]
        
        except websockets.ConnectionClosed:
            self.logger.debug("WebSocket连接已关闭")
        except Exception as e:
            self.logger.error(f"WebSocket处理错误: {e}")
        finally:
            # 清理连接
            if websocket in self.websocket_users:
                self.websocket_users.remove(websocket)
                await self.ws_reset(websocket)

    async def start_server(self):
        """启动WebSocket服务器"""
        server = await websockets.serve(
            self.handle_websocket, 
            self.host, 
            self.port, 
            subprotocols=["binary"],
            ping_interval=None
        )
        
        self.logger.info(f"FunASR服务器已启动，监听地址: {self.host}:{self.port}")
        self.is_running = True
        
        # 保持服务器运行
        try:
            await asyncio.Future()
        finally:
            server.close()
            await server.wait_closed()
            self.is_running = False
            self.logger.info("FunASR服务器已关闭")

    def start(self):
        """启动服务器（非阻塞方式）"""
        if self.is_running:
            self.logger.info("FunASR服务器已在运行")
            return True
            
        # 加载模型
        if not self.load_models():
            return False
            
        # 创建事件循环
        def run_server():
            asyncio.run(self.start_server())
            
        # 在新线程中启动服务器
        self.server_thread = threading.Thread(
            target=run_server,
            daemon=True
        )
        self.server_thread.start()
        
        # 等待一会儿，确保服务器启动
        time.sleep(3)
        return True

    def stop(self):
        """停止服务器"""
        if not self.is_running:
            return
            
        self.logger.info("正在停止FunASR服务器...")
        self.is_running = False
        
        # 释放资源
        self.model_asr = None
        self.model_asr_streaming = None
        self.model_vad = None
        self.model_punc = None
        
        self.logger.info("FunASR服务器已停止")
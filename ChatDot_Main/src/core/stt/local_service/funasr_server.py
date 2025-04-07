"""
FunASR WebSocket服务器实现
基于原始的funasr_wss_server.py改造
"""
import asyncio
import json
import websockets
import threading
import time
from typing import Set, Dict, Any
from global_managers.logger_manager import LoggerManager

class FunASRServer:
    """FunASR WebSocket服务器类"""
    
    def __init__(self):
        """初始化FunASR服务器"""
        self.host = "localhost"
        self.port = 10095
        self.device = "cuda"
        self.ngpu = 1
        self.ncpu = 4
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
        """
        设置服务器配置
        
        Args:
            host: 服务器地址
            port: 服务器端口
            device: 设备类型
            ngpu: GPU数量
            ncpu: CPU核心数
            models: 模型配置
        """
        self.host = host
        self.port = port
        self.device = device
        self.ngpu = ngpu
        self.ncpu = ncpu
        
        if models:
            self.models.update(models)
            
    def load_models(self):
        """
        加载FunASR模型
        
        Returns:
            bool: 是否成功加载模型
        """
        self.logger.info("正在加载FunASR模型...")
        
        try:
            # 导入FunASR
            try:
                from funasr import AutoModel
            except ImportError:
                self.logger.error("未找到FunASR库，请使用 'pip install funasr' 安装")
                return False
            
            # 加载ASR模型
            self.model_asr = AutoModel(
                model=self.models["asr_model"],
                model_revision=self.models["asr_model_revision"],
                device=self.device,
                ngpu=self.ngpu if self.device == "cuda" else 0,
                ncpu=self.ncpu,
                disable_pbar=True,
                disable_log=True,
            )
            self.logger.debug("ASR模型加载完成")
            
            # 加载在线ASR模型
            self.model_asr_streaming = AutoModel(
                model=self.models["asr_model_online"],
                model_revision=self.models["asr_model_online_revision"],
                device=self.device,
                ngpu=self.ngpu if self.device == "cuda" else 0,
                ncpu=self.ncpu,
                disable_pbar=True,
                disable_log=True,
            )
            self.logger.debug("在线ASR模型加载完成")
            
            # 加载VAD模型
            self.model_vad = AutoModel(
                model=self.models["vad_model"],
                model_revision=self.models["vad_model_revision"],
                device=self.device,
                ngpu=self.ngpu if self.device == "cuda" else 0,
                ncpu=self.ncpu,
                disable_pbar=True,
                disable_log=True,
            )
            self.logger.debug("VAD模型加载完成")
            
            # 加载标点模型
            self.model_punc = AutoModel(
                model=self.models["punc_model"],
                model_revision=self.models["punc_model_revision"],
                device=self.device,
                ngpu=self.ngpu if self.device == "cuda" else 0,
                ncpu=self.ncpu,
                disable_pbar=True,
                disable_log=True,
            )
            self.logger.debug("标点模型加载完成")
                
            self.logger.info("所有FunASR模型加载完成")
            return True
            
        except Exception as e:
            self.logger.error(f"加载FunASR模型失败: {str(e)}")
            return False
            
    async def ws_reset(self, websocket):
        """
        重置WebSocket连接
        
        Args:
            websocket: WebSocket连接
        """
        self.logger.debug(f"重置WebSocket连接，当前连接数: {len(self.websocket_users)}")
        
        if hasattr(websocket, "status_dict_asr_online"):
            websocket.status_dict_asr_online["cache"] = {}
            websocket.status_dict_asr_online["is_final"] = True
            
        if hasattr(websocket, "status_dict_vad"):
            websocket.status_dict_vad["cache"] = {}
            websocket.status_dict_vad["is_final"] = True
            
        if hasattr(websocket, "status_dict_punc"):
            websocket.status_dict_punc["cache"] = {}
        
        await websocket.close()

    async def async_vad(self, websocket, audio_in):
        """
        语音活动检测
        
        Args:
            websocket: WebSocket连接
            audio_in: 音频数据
            
        Returns:
            tuple: (speech_start, speech_end)
        """
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
        """
        离线ASR处理
        
        Args:
            websocket: WebSocket连接
            audio_in: 音频数据
        """
        if len(audio_in) > 0:
            rec_result = self.model_asr.generate(input=audio_in, **websocket.status_dict_asr)[0]
            
            # 如果有标点模型且识别到文本，应用标点
            if self.model_punc is not None and len(rec_result["text"]) > 0:
                rec_result = self.model_punc.generate(
                    input=rec_result["text"], **websocket.status_dict_punc
                )[0]
                
            # 发送结果
            if len(rec_result["text"]) > 0:
                mode = "2pass-offline" if "2pass" in websocket.mode else websocket.mode
                message = json.dumps(
                    {
                        "mode": mode,
                        "text": rec_result["text"],
                        "wav_name": websocket.wav_name,
                        "is_final": True,  # 明确标记为最终结果
                    }
                )
                await websocket.send(message)
        else:
            # 发送空结果
            mode = "2pass-offline" if "2pass" in websocket.mode else websocket.mode
            message = json.dumps(
                {
                    "mode": mode,
                    "text": "",
                    "wav_name": websocket.wav_name,
                    "is_final": True,
                }
            )
            await websocket.send(message)

    async def async_asr_online(self, websocket, audio_in):
        """
        在线ASR处理
        
        Args:
            websocket: WebSocket连接
            audio_in: 音频数据
        """
        if len(audio_in) > 0:
            rec_result = self.model_asr_streaming.generate(
                input=audio_in, **websocket.status_dict_asr_online
            )[0]
            
            # 2pass模式下，如果是最终结果，不发送在线结果
            if websocket.mode == "2pass" and websocket.status_dict_asr_online.get("is_final", False):
                return
                
            # 发送结果
            if len(rec_result["text"]):
                mode = "2pass-online" if "2pass" in websocket.mode else websocket.mode
                message = json.dumps(
                    {
                        "mode": mode,
                        "text": rec_result["text"],
                        "wav_name": websocket.wav_name,
                        "is_final": False,  # 明确标记为非最终结果
                    }
                )
                await websocket.send(message)

    async def handle_websocket(self, websocket, path=None):
        """
        处理WebSocket连接
        
        Args:
            websocket: WebSocket连接
            path: 路径
        """
        frames = []
        frames_asr = []
        frames_asr_online = []
        
        # 添加到用户集合
        self.websocket_users.add(websocket)
        
        # 初始化状态
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
        
        self.logger.debug(f"新WebSocket连接，当前连接数: {len(self.websocket_users)}")
        
        try:
            async for message in websocket:
                # 处理字符串消息（配置消息）
                if isinstance(message, str):
                    try:
                        messagejson = json.loads(message)
                        
                        # 处理各种配置参数
                        if "is_speaking" in messagejson:
                            websocket.is_speaking = messagejson["is_speaking"]
                            websocket.status_dict_asr_online["is_final"] = not websocket.is_speaking
                        if "chunk_interval" in messagejson:
                            websocket.chunk_interval = messagejson["chunk_interval"]
                        if "wav_name" in messagejson:
                            websocket.wav_name = messagejson.get("wav_name")
                        if "chunk_size" in messagejson:
                            chunk_size = messagejson["chunk_size"]
                            if isinstance(chunk_size, str):
                                chunk_size = chunk_size.split(",")
                            websocket.status_dict_asr_online["chunk_size"] = [int(x) for x in chunk_size]
                        if "encoder_chunk_look_back" in messagejson:
                            websocket.status_dict_asr_online["encoder_chunk_look_back"] = messagejson[
                                "encoder_chunk_look_back"
                            ]
                        if "decoder_chunk_look_back" in messagejson:
                            websocket.status_dict_asr_online["decoder_chunk_look_back"] = messagejson[
                                "decoder_chunk_look_back"
                            ]
                        if "hotwords" in messagejson:
                            websocket.status_dict_asr["hotword"] = messagejson["hotwords"]
                        if "mode" in messagejson:
                            websocket.mode = messagejson["mode"]
                    except json.JSONDecodeError:
                        self.logger.error(f"无效的JSON消息: {message}")
                        continue
                    
                # VAD分块大小设置
                if hasattr(websocket, "status_dict_asr_online") and "chunk_size" in websocket.status_dict_asr_online:
                    try:
                        websocket.status_dict_vad["chunk_size"] = int(
                            websocket.status_dict_asr_online["chunk_size"][1] * 60 / websocket.chunk_interval
                        )
                    except (IndexError, ZeroDivisionError):
                        websocket.status_dict_vad["chunk_size"] = 60
                
                # 处理二进制音频数据
                if (len(frames_asr_online) > 0 or len(frames_asr) >= 0 
                    or (not isinstance(message, str) and message)):
                    
                    if not isinstance(message, str) and message:
                        frames.append(message)
                        duration_ms = len(message) // 32
                        websocket.vad_pre_idx += duration_ms
                        
                        # ASR在线处理
                        frames_asr_online.append(message)
                        websocket.status_dict_asr_online["is_final"] = speech_end_i != -1
                        
                        if (len(frames_asr_online) % websocket.chunk_interval == 0
                            or websocket.status_dict_asr_online["is_final"]):
                            
                            if websocket.mode == "2pass" or websocket.mode == "online":
                                audio_in = b"".join(frames_asr_online)
                                try:
                                    await self.async_asr_online(websocket, audio_in)
                                except Exception as e:
                                    self.logger.error(f"在线ASR处理出错: {e}")
                            frames_asr_online = []
                        
                        # 如果检测到语音开始，就累积帧
                        if speech_start:
                            frames_asr.append(message)
                            
                        # VAD处理
                        try:
                            speech_start_i, speech_end_i = await self.async_vad(websocket, message)
                        except Exception as e:
                            self.logger.error(f"VAD处理出错: {e}")
                            speech_start_i, speech_end_i = -1, -1
                            
                        # 如果检测到语音开始
                        if speech_start_i != -1:
                            speech_start = True
                            beg_bias = (websocket.vad_pre_idx - speech_start_i) // duration_ms
                            frames_pre = frames[-min(beg_bias, len(frames)):]
                            frames_asr = []
                            frames_asr.extend(frames_pre)
                            
                    # 如果检测到语音结束或用户停止说话
                    if speech_end_i != -1 or not websocket.is_speaking:
                        # 离线ASR处理
                        if websocket.mode == "2pass" or websocket.mode == "offline":
                            audio_in = b"".join(frames_asr)
                            try:
                                await self.async_asr(websocket, audio_in)
                            except Exception as e:
                                self.logger.error(f"离线ASR处理出错: {e}")
                                
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
                            frames = frames[-min(20, len(frames)):]  # 保留最近的几帧
                        
        except websockets.ConnectionClosed:
            self.logger.debug(f"WebSocket连接已关闭，当前连接数: {len(self.websocket_users) - 1}")
        except Exception as e:
            self.logger.error(f"处理WebSocket连接时出错: {str(e)}")
        finally:
            if websocket in self.websocket_users:
                self.websocket_users.remove(websocket)
                try:
                    await self.ws_reset(websocket)
                except:
                    pass

    async def run_server(self):
        """运行WebSocket服务器"""
        try:
            self.logger.info(f"正在启动FunASR服务器，监听地址: {self.host}:{self.port}")
            
            server = await websockets.serve(
                self.handle_websocket, 
                self.host, 
                self.port, 
                subprotocols=["binary"],
                ping_interval=None
            )
            
            self.is_running = True
            self.logger.info(f"FunASR服务器已启动，监听地址: {self.host}:{self.port}")
            
            # 保持服务器运行
            while self.is_running:
                await asyncio.sleep(1)
                
            # 关闭服务器
            self.logger.info("正在关闭FunASR服务器...")
            server.close()
            await server.wait_closed()
            self.logger.info("FunASR服务器已关闭")
            
        except Exception as e:
            self.logger.error(f"服务器运行时出错: {str(e)}")
            self.is_running = False

    def start(self):
        """
        非阻塞启动服务器
        
        Returns:
            bool: 是否成功启动
        """
        if self.is_running:
            self.logger.info("FunASR服务器已在运行")
            return True
            
        # 加载模型
        if not self.load_models():
            return False
            
        # 创建并启动新线程运行服务器
        def run_server():
            asyncio.run(self.run_server())
            
        self.server_thread = threading.Thread(
            target=run_server,
            daemon=True
        )
        self.server_thread.start()
        
        # 等待服务器启动
        time.sleep(2)
        return True

    def stop(self):
        """停止服务器"""
        if not self.is_running:
            return
            
        self.is_running = False
        time.sleep(2)  # 等待服务器关闭
        
        # 释放资源
        self.model_asr = None
        self.model_asr_streaming = None
        self.model_vad = None
        self.model_punc = None
        
        self.logger.info("FunASR服务器资源已释放")
"""
FunASR 客户端
处理与FunASR服务器的通信
"""

import asyncio
import json
import pyaudio
import websockets
import time
import numpy as np
from typing import Callable, List, Optional
from global_managers.logger_manager import LoggerManager

class STTClient:
    """
    STT客户端，处理与FunASR服务器的通信
    """
    
    def __init__(self):
        """初始化STT客户端"""
        self.host = "localhost"
        self.port = 10095
        self.use_ssl = False
        self.websocket = None
        self.is_running = False
        self.segment_callbacks: List[Callable[[str], None]] = []
        self.logger = LoggerManager().get_logger()
        
        self.volume_threshold = 300  # 默认音量阈值
        self.silence_timeout = 1.5   # 默认沉默超时时间(秒)
        self.last_sound_time = 0     # 最后一次检测到声音的时间
        
    def set_audio_params(self, volume_threshold=None, silence_timeout=None):
        """
        设置音频参数
        
        Args:
            volume_threshold: 音量阈值，0-32767之间的值
            silence_timeout: 沉默超时时间(秒)
        """
        if volume_threshold is not None:
            self.volume_threshold = max(0, min(32767, volume_threshold))
        if silence_timeout is not None:
            self.silence_timeout = max(0.1, silence_timeout)
            
    def _get_audio_volume(self, audio_data):
        """
        获取音频数据的音量
        
        Args:
            audio_data: 二进制音频数据
            
        Returns:
            float: 音频音量值
        """
        try:
            # 将字节转换为16位整数数组
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            if len(audio_array) == 0:
                return 0.0
                
            # 计算音频的RMS值作为音量，使用float64避免溢出
            square_sum = np.mean(np.square(audio_array.astype(np.float64)))
            
            # 确保非负值
            if square_sum <= 0:
                return 0.0
                
            return np.sqrt(square_sum)
        except Exception as e:
            self.logger.error(f"计算音频音量时出错: {e}")
            return 0.0
        
    def set_server(self, host: str, port: int, use_ssl: bool = False) -> None:
        """
        设置服务器参数
        
        Args:
            host: 服务器地址
            port: 服务器端口
            use_ssl: 是否使用SSL连接
        """
        self.host = host
        self.port = port
        self.use_ssl = use_ssl

    def add_segment_callback(self, callback: Callable[[str], None]) -> None:
        """
        添加语音片段回调函数
        
        Args:
            callback: 回调函数，接收完整的语音识别结果文本
        """
        self.segment_callbacks.append(callback)

    async def record_microphone(self, websocket) -> None:
        """从麦克风录制音频并发送到服务器"""
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK_MS = 60  # 每个音频块的毫秒数
        CHUNK = int(RATE / 1000 * CHUNK_MS)
        
        # 跟踪是否正在说话
        is_speaking = False
        has_sent_config = False
        silence_start_time = 0

        p = pyaudio.PyAudio()
        stream = None
        
        try:
            # 打开麦克风流
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            # 发送初始配置消息
            config = {
                "mode": "2pass",
                "chunk_size": [5, 10, 5],
                "chunk_interval": 10,
                "encoder_chunk_look_back": 4,
                "decoder_chunk_look_back": 0,
                "wav_name": "microphone",
                "is_speaking": False,  # 默认先设为False，等检测到声音再开始
                "hotwords": "",
                "itn": True
            }
            
            await websocket.send(json.dumps(config))
            self.logger.debug("已发送FunASR初始配置")

            # 持续发送音频数据
            while self.is_running:
                if stream.is_stopped():
                    stream.start_stream()
                    
                data = stream.read(CHUNK, exception_on_overflow=False)
                
                # 计算当前音频块的音量
                volume = self._get_audio_volume(data)
                current_time = time.time()
                
                # 如果音量超过阈值，认为有效声音
                if volume > self.volume_threshold:
                    if not is_speaking:
                        # 状态从不说话变为说话
                        self.logger.debug(f"检测到有效声音: {volume:.2f}, 阈值: {self.volume_threshold}")
                        is_speaking = True
                        # 通知服务器开始说话
                        config["is_speaking"] = True
                        await websocket.send(json.dumps(config))
                        
                    # 更新最后检测到声音的时间
                    self.last_sound_time = current_time
                    
                    # 发送音频数据
                    if self.is_running:  # 避免在关闭后仍继续发送数据
                        await websocket.send(data)
                else:
                    # 音量低于阈值，检查是否需要结束当前语音片段
                    if is_speaking and (current_time - self.last_sound_time > self.silence_timeout):
                        # 沉默超过timeout，认为说话结束
                        self.logger.debug("检测到沉默超时，停止当前语音片段")
                        is_speaking = False
                        # 通知服务器停止说话
                        config["is_speaking"] = False
                        await websocket.send(json.dumps(config))
                    elif is_speaking:
                        # 虽然是沉默，但还在说话状态内，继续发送数据
                        if self.is_running:
                            await websocket.send(data)
                    
                await asyncio.sleep(0.01)
                
        except Exception as e:
            self.logger.error(f"录音错误: {e}")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
            p.terminate()
            self.logger.debug("已停止录音")
    
    async def handle_messages(self, websocket) -> None:
        """
        处理服务器返回的消息
        
        Args:
            websocket: WebSocket连接
        """
        while self.is_running:
            try:
                msg = await websocket.recv()
                data = json.loads(msg)
                
                text = data.get("text", "")
                is_final = data.get("is_final", False)
                mode = data.get("mode", "")
                
                # 只处理2pass-offline模式的最终结果
                if is_final and mode == "2pass-offline" and text:
                    # 触发所有回调函数
                    for callback in self.segment_callbacks:
                        try:
                            callback(text)
                        except Exception as e:
                            self.logger.error(f"回调函数执行错误: {e}")
                        
            except Exception as e:
                if self.is_running:
                    self.logger.error(f"处理消息错误: {e}")
                await asyncio.sleep(0.1)

    async def connect(self) -> bool:
        """
        连接到FunASR服务器
        
        Returns:
            bool: 连接是否成功
        """
        if self.use_ssl:
            import ssl
            ssl_context = ssl.SSLContext()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = f"wss://{self.host}:{self.port}"
        else:
            uri = f"ws://{self.host}:{self.port}"
            ssl_context = None
        
        try:
            self.logger.info(f"连接到FunASR服务: {uri}")
            self.websocket = await websockets.connect(
                uri, 
                subprotocols=["binary"], 
                ping_interval=None, 
                ssl=ssl_context
            )
            self.logger.info("已成功连接到FunASR服务")
            return True
        except Exception as e:
            self.logger.error(f"连接FunASR服务失败: {e}")
            return False

    async def start(self) -> None:
        """启动语音识别"""
        self.is_running = True
        
        # 重试逻辑
        max_retries = 3
        retry_count = 0
        retry_delay = 1  # 秒
        
        while retry_count < max_retries and self.is_running:
            try:
                async with websockets.connect(
                    f"ws://{self.host}:{self.port}" if not self.use_ssl else f"wss://{self.host}:{self.port}",
                    subprotocols=["binary"],
                    ping_interval=None
                ) as websocket:
                    self.logger.info(f"已成功连接到FunASR服务: {self.host}:{self.port}")
                    
                    # 并行运行音频录制和消息处理
                    record_task = asyncio.create_task(self.record_microphone(websocket))
                    message_task = asyncio.create_task(self.handle_messages(websocket))
                    
                    # 等待任务完成或取消
                    done, pending = await asyncio.wait(
                        [record_task, message_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # 取消未完成的任务
                    for task in pending:
                        task.cancel()
                    
                    # 如果正常退出，结束重试循环
                    if not self.is_running:
                        break
                    
                    # 否则，准备重试
                    retry_count += 1
                    if retry_count < max_retries:
                        self.logger.warning(f"连接中断，{retry_delay}秒后重试 ({retry_count}/{max_retries})...")
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 5)
                    
            except ConnectionRefusedError:
                retry_count += 1
                if retry_count >= max_retries:
                    self.logger.error(f"无法连接到FunASR服务: {self.host}:{self.port}，已达最大重试次数")
                    self.is_running = False
                    break
                
                self.logger.warning(f"无法连接到FunASR服务，{retry_delay}秒后重试 ({retry_count}/{max_retries})...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 5)
                
            except Exception as e:
                self.logger.error(f"STT客户端错误: {e}")
                self.is_running = False
                break

    def stop(self) -> None:
        """停止语音识别"""
        self.is_running = False
        self.logger.info("已停止语音识别")

    def is_active(self) -> bool:
        """
        检查客户端是否活动
        
        Returns:
            bool: 客户端是否正在运行
        """
        return self.is_running
"""
FunASR客户端类，与原始funasr_demo.py保持一致
"""
import asyncio
import json
import pyaudio
import websockets
import time
from typing import Callable, List
from global_managers.logger_manager import LoggerManager

class FunASRClient:
    def __init__(self, host: str = "localhost", port: int = 10095, use_ssl: bool = False):
        """
        初始化FunASR客户端
        
        Args:
            host: 服务器地址
            port: 服务器端口
            use_ssl: 是否使用SSL连接
        """
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.is_running = False
        self.segment_callbacks: List[Callable[[str], None]] = []
        self.logger = LoggerManager().get_logger()

    def add_segment_callback(self, callback: Callable[[str], None]) -> None:
        """添加只接收完整结果的回调函数"""
        self.segment_callbacks.append(callback)

    async def record_microphone(self, websocket) -> None:
        """从麦克风录制音频并发送到服务器"""
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK = int(RATE / 1000 * 60)

        p = pyaudio.PyAudio()
        stream = None
        try:
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )

            # 发送初始配置消息
            message = json.dumps({
                "mode": "2pass",
                "chunk_size": [5, 10, 5],
                "chunk_interval": 10,
                "encoder_chunk_look_back": 4,
                "decoder_chunk_look_back": 0,
                "wav_name": "microphone",
                "is_speaking": True,
                "hotwords": "",
                "itn": True,
            })
            await websocket.send(message)
            self.logger.debug("已发送初始配置")

            while self.is_running:
                data = stream.read(CHUNK, exception_on_overflow=False)
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
        """处理从服务器接收的消息"""
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
                        callback(text)
                        
            except Exception as e:
                self.logger.error(f"处理消息错误: {e}")
                break

    async def start(self) -> None:
        """启动语音识别"""
        self.is_running = True
        
        if self.use_ssl:
            import ssl
            ssl_context = ssl.SSLContext()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = f"wss://{self.host}:{self.port}"
        else:
            uri = f"ws://{self.host}:{self.port}"
            ssl_context = None
            
        self.logger.info(f"连接到FunASR服务: {uri}")
        
        # 增加重连逻辑
        max_retries = 3
        retry_count = 0
        retry_delay = 1  # 秒
        
        while retry_count < max_retries and self.is_running:
            try:
                async with websockets.connect(
                    uri, subprotocols=["binary"], ping_interval=None, ssl=ssl_context
                ) as websocket:
                    self.logger.info("已连接到FunASR服务")
                    
                    # 并行运行音频录制和消息处理
                    await asyncio.gather(
                        self.record_microphone(websocket),
                        self.handle_messages(websocket)
                    )
                    
                # 如果正常退出循环，说明连接已关闭
                break
                    
            except ConnectionRefusedError:
                retry_count += 1
                if retry_count >= max_retries:
                    self.logger.error(f"无法连接到FunASR服务: {uri}，已达到最大重试次数")
                    self.is_running = False
                    break
                
                self.logger.warning(f"无法连接到FunASR服务: {uri}，{retry_delay}秒后重试 ({retry_count}/{max_retries})...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
                
            except Exception as e:
                self.logger.error(f"FunASR客户端错误: {e}")
                self.is_running = False
                break

    def stop(self) -> None:
        """停止语音识别"""
        self.is_running = False
        self.logger.info("已停止语音识别")
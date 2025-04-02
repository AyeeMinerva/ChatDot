import asyncio
import sys
import os
import json
import pyaudio
import websockets
import ssl
from typing import Callable, List, Dict, Any

class RealtimeASR:
    def __init__(self, host: str = "localhost", port: int = 10095, use_ssl: bool = False):
        """
        初始化实时语音识别类
        
        Args:
            host: 服务器地址
            port: 服务器端口
            use_ssl: 是否使用SSL连接
        """
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.websocket = None
        self.is_running = False
        self.current_text = ""
        self.final_text = ""
        self.callbacks: List[Callable[[str, bool], None]] = []
        self.last_segment = ""  # 添加新变量存储最后一个完整的识别片段
        self.segment_callbacks: List[Callable[[str], None]] = []  # 新增完整片段的回调

    def add_callback(self, callback: Callable[[str, bool], None]) -> None:
        """
        添加回调函数以接收识别结果
        
        Args:
            callback: 回调函数，接收参数(text: str, is_final: bool)
        """
        self.callbacks.append(callback)

    def get_current_result(self) -> Dict[str, Any]:
        """获取当前实时识别结果"""
        return {
            "text": self.current_text,
            "is_final": False
        }

    def get_final_result(self) -> Dict[str, Any]:
        """获取最终识别结果"""
        return {
            "text": self.final_text,
            "is_final": True
        }

    async def record_microphone(self, websocket) -> None:
        """音频采集功能"""
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        chunk_size = 60 * 10 / 10  # 使用默认参数
        CHUNK = int(RATE / 1000 * chunk_size)

        p = pyaudio.PyAudio()
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

        try:
            while self.is_running:
                data = stream.read(CHUNK)
                await websocket.send(data)
                await asyncio.sleep(0.005)
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    async def handle_messages(self, websocket) -> None:
        """处理服务器返回的消息"""
        while self.is_running:
            try:
                msg = await websocket.recv()
                msg = json.loads(msg)
                
                # 打印原始 JSON 消息（调试用）
                # print("\n收到的 JSON 包:")
                # print(json.dumps(msg, ensure_ascii=False, indent=2))
                
                text = msg.get("text", "")
                is_final = msg.get("is_final", False)
                mode = msg.get("mode", "")
                
                # 收到的包有 2pass-online 和 2pass-offline 两种模式
                # 2pass-online 模式返回的较快，但不完整
                # 2pass-offline 模式返回的较慢，但完整
                # 这里只处理 2pass-offline 模式的最终结果
                if is_final and mode == "2pass-offline":
                    self.last_segment = text
                    
                    # 触发完整片段回调
                    for callback in self.segment_callbacks:
                        callback(text)
                    
                    # 触发一般回调
                    for callback in self.callbacks:
                        callback(text, True)
                    
                elif not is_final:
                    self.current_text = text
                    
            except Exception as e:
                print(f"\n接收消息错误: {e}")
                break

    async def start(self) -> None:
        """启动实时语音识别"""
        self.is_running = True
        
        if self.use_ssl:
            ssl_context = ssl.SSLContext()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = f"wss://{self.host}:{self.port}"
        else:
            uri = f"ws://{self.host}:{self.port}"
            ssl_context = None
            
        print(f"正在连接服务器: {uri}")
        
        async with websockets.connect(
            uri, subprotocols=["binary"], ping_interval=None, ssl=ssl_context
        ) as websocket:
            # 创建音频采集和结果处理任务
            audio_task = asyncio.create_task(self.record_microphone(websocket))
            message_task = asyncio.create_task(self.handle_messages(websocket))
            
            # 等待任务完成
            try:
                await asyncio.gather(audio_task, message_task)
            except asyncio.CancelledError:
                self.is_running = False
    
    def run(self) -> None:
        """运行实时语音识别"""
        try:
            asyncio.get_event_loop().run_until_complete(self.start())
        except KeyboardInterrupt:
            print("\n停止语音识别...")
        finally:
            self.is_running = False

    def add_segment_callback(self, callback: Callable[[str], None]) -> None:
        """添加只接收完整语音片段的回调函数"""
        self.segment_callbacks.append(callback)

    def get_last_segment(self) -> str:
        """获取最后一个完整的识别片段"""
        return self.last_segment

def segment_callback(text: str) -> None:
    """只接收 2pass-offline 模式的完整结果"""
    print(f"\n收到 2pass-offline 最终结果: {text}")

async def main():
    asr = RealtimeASR(
        host="localhost",
        port=10095,
        use_ssl=False
    )
    
    asr.add_segment_callback(segment_callback)
    print("开始语音识别，只显示 2pass-offline 模式的最终结果...")
    await asr.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n停止语音识别...")
    except Exception as e:
        print(f"发生错误: {e}")
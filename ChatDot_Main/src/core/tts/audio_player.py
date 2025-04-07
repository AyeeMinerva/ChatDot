import pyaudio
import queue
import threading
import io
import wave
import time
import numpy as np
from global_managers.logger_manager import LoggerManager

class AudioPlayer:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.audio_queue = queue.Queue()
            self.play_thread = None
            self.stop_flag = False
            self.first_chunk = True
            self.pyaudio = pyaudio.PyAudio()
            self.stream = None
            self.initialized = True
            #LoggerManager().get_logger().debug("AudioPlayer 初始化完成")

    def start(self):
        """启动播放线程"""
        if self.play_thread is None or not self.play_thread.is_alive():
            self.stop_flag = False
            self.first_chunk = True  # 重置标志，用于识别头部WAV
            self.play_thread = threading.Thread(target=self._play_from_queue)
            self.play_thread.daemon = True
            self.play_thread.start()
            #LoggerManager().get_logger().debug("音频播放线程已启动")

    def is_playing(self):
        """检查是否有音频正在播放"""
        return self.stream is not None and self.stream.is_active() or not self.audio_queue.empty()

    def stop(self):
        """停止播放"""
        self.stop_flag = True
        
        # 清空队列
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        # 停止并关闭流
        if self.stream:
            if self.stream.is_active():
                self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        #LoggerManager().get_logger().debug("音频播放已停止")

    def _play_from_queue(self):
        """从队列中获取并播放音频数据"""
        while not self.stop_flag:
            try:
                # 非阻塞方式获取数据
                try:
                    chunk = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # 检查是否为WAV数据
                if len(chunk) >= 44 and chunk.startswith(b'RIFF'):
                    LoggerManager().get_logger().debug("收到WAV头部数据，开始播放音频")
                    # 解析WAV头获取音频参数
                    wav_file = wave.open(io.BytesIO(chunk))
                    
                    # 如果流存在且参数不同，则关闭重建
                    if self.stream:
                        self.stream.stop_stream()
                        self.stream.close()
                    
                    # 创建新的音频流
                    self.stream = self.pyaudio.open(
                        format=self.pyaudio.get_format_from_width(wav_file.getsampwidth()),
                        channels=wav_file.getnchannels(),
                        rate=wav_file.getframerate(),
                        output=True
                    )
                    
                    # 跳过WAV头，播放剩余部分
                    if len(chunk) > 44:
                        audio_data = chunk[44:]
                        if audio_data and self.stream:
                            self.stream.write(audio_data)
                else:
                    # 如果是音频数据，直接播放
                    if self.stream:
                        self.stream.write(chunk)
                    
            except Exception as e:
                LoggerManager().get_logger().warning(f"tts/audio_player: 音频播放错误: {e}")
    

    def feed_data(self, audio_data: bytes):
        """添加音频数据到播放队列"""
        if audio_data:
            self.audio_queue.put(audio_data)

    def __del__(self):
        """析构函数，确保资源释放"""
        if hasattr(self, 'pyaudio') and self.pyaudio:
            if hasattr(self, 'stream') and self.stream:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
            self.pyaudio.terminate()

    @classmethod
    def get_instance(cls):
        """获取AudioPlayer单例"""
        if cls._instance is None:
            cls._instance = AudioPlayer()
        return cls._instance

# 创建全局播放器实例
player = AudioPlayer.get_instance()


if __name__ == "__main__":
    import os
    
    # 测试音频播放
    def test_play_audio(wav_path):
        LoggerManager().get_logger().debug(f"\n开始播放音频: {wav_path}")
        
        # 获取播放器实例
        player = AudioPlayer.get_instance()
        player.start()
        
        try:
            # 读取WAV文件
            with open(wav_path, 'rb') as f:
                audio_data = f.read()
                
            # 连续播放3次
            for i in range(3):
                LoggerManager().get_logger().debug(f"\n第 {i+1} 次播放")
                player.feed_data(audio_data)
                # 等待2秒
                time.sleep(2)
                
        except Exception as e:
            LoggerManager().get_logger().warning(f"播放出错: {e}")
        finally:
            player.stop()
    
    # 测试用的WAV文件路径 
    wav_path = r"D:\jiajingyi\projects\ChatDot\ChatDot_Main\Refactoring_src\core\tts\测试.wav"
    
    if os.path.exists(wav_path):
        test_play_audio(wav_path)
    else:
        LoggerManager().get_logger().warning(f"测试文件不存在: {wav_path}")
        LoggerManager().get_logger().warning("请修改为正确的WAV文件路径")
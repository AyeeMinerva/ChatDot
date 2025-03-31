import pyaudio
import queue
import threading
import io
import wave
import time

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
            #print("AudioPlayer 初始化完成")

    def start(self):
        """启动播放线程"""
        if self.play_thread is None or not self.play_thread.is_alive():
            self.stop_flag = False
            self.first_chunk = True  # 重置标志，用于识别头部WAV
            self.play_thread = threading.Thread(target=self._play_from_queue)
            self.play_thread.daemon = True
            self.play_thread.start()
            #print("音频播放线程已启动")

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
        
        #print("音频播放已停止")

    def _play_from_queue(self):
        """从队列中获取并播放音频数据"""
        #print("播放线程开始运行")
        
        while not self.stop_flag:
            try:
                # 非阻塞方式获取数据
                try:
                    chunk = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # 处理第一个数据块(WAV头)
                if self.first_chunk and len(chunk) >= 44 and chunk.startswith(b'RIFF'):
                    #print(f"收到WAV头部数据，大小: {len(chunk)} 字节")
                    # 解析WAV头获取音频参数
                    wav_file = wave.open(io.BytesIO(chunk))
                    
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
                    self.first_chunk = False
                    
                    # 跳过WAV头，播放剩余部分
                    if len(chunk) > 44:
                        audio_data = chunk[44:]
                        if audio_data and self.stream:
                            self.stream.write(audio_data)
                else:
                    # 播放后续数据块
                    if chunk and self.stream:
                        self.stream.write(chunk)
                
            except Exception as e:
                print(f"tts/audio_player: 音频播放错误: {e}")

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
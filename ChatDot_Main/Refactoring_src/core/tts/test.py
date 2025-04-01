import requests
import wave
import pyaudio
import io
import threading
import queue
import time

def stream_audio_request(text, text_lang, ref_audio_path, prompt_lang, prompt_text):
    """发送流式合成请求并返回音频数据生成器"""
    url = "http://183.175.12.68:9880/tts"
    
    params = {
        "text": text,
        "text_lang": text_lang,
        "ref_audio_path": ref_audio_path,
        "prompt_lang": prompt_lang,
        "prompt_text": prompt_text,
        "text_split_method": "cut5",
        "batch_size": 1,
        "media_type": "wav",
        "streaming_mode": True
    }
    
    # 使用stream模式发送请求
    response = requests.post(url, json=params, stream=True)
    if response.status_code != 200:
        raise Exception(f"请求失败: {response.status_code}")
        
    return response.iter_content(chunk_size=1024)

def play_audio_stream(audio_queue):
    """从队列中读取并播放音频数据"""
    p = pyaudio.PyAudio()
    first_chunk = True
    stream = None
    
    try:
        while True:
            chunk = audio_queue.get()
            if chunk is None:  # 结束标记
                break
                
            # 处理第一个数据块(WAV头)
            if first_chunk:
                # 解析WAV头获取音频参数
                wav_file = wave.open(io.BytesIO(chunk))
                stream = p.open(
                    format=p.get_format_from_width(wav_file.getsampwidth()),
                    channels=wav_file.getnchannels(),
                    rate=wav_file.getframerate(),
                    output=True
                )
                first_chunk = False
                # 跳过WAV头
                chunk = chunk[44:]
            
            if chunk:  # 播放音频数据
                stream.write(chunk)
                
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        p.terminate()

def main():
    # 创建音频数据队列
    audio_queue = queue.Queue()
    
    # 启动播放线程
    play_thread = threading.Thread(target=play_audio_stream, args=(audio_queue,))
    play_thread.start()
    
    try:
        # 发送TTS请求
        audio_stream = stream_audio_request(
            text="先帝创业未半而中道崩殂，今天下三分，益州疲弊，此诚危急存亡之秋也。",
            text_lang="zh",
            ref_audio_path="/data/qinxu/GPT-SoVITS/sample_audios/37_也许过大的目标会导致逻辑上的越界.wav",
            prompt_lang="zh",
            prompt_text="也许过大的目标会导致逻辑上的越界"
        )
        
        # 处理音频流
        for chunk in audio_stream:
            audio_queue.put(chunk)
            time.sleep(0.01)  # 控制数据发送速率
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        # 发送结束标记
        audio_queue.put(None)
        # 等待播放线程结束
        play_thread.join()

if __name__ == "__main__":
    main()
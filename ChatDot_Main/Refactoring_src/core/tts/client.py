import requests

class TTSClient:
    def __init__(self, server_url: str = None):
        """
        初始化 TTS 客户端
        :param server_url: TTS 后端的服务器地址
        """
        self.server_url = server_url

    def set_server_url(self, server_url: str):
        """
        设置 TTS 后端的服务器地址
        :param server_url: TTS 后端的服务器地址
        """
        self.server_url = server_url

    def synthesize(self, text: str, text_lang: str, ref_audio_path: str, prompt_lang: str, prompt_text: str, text_split_method: str, batch_size: int, media_type: str, streaming_mode: bool):
        """
        调用 TTS 后端进行语音合成（非流式）
        """
        if not self.server_url:
            raise ValueError("TTS 后端 URL 未设置")

        url = f"{self.server_url}/tts"
        params = {
            "text": text,
            "text_lang": text_lang,
            "ref_audio_path": ref_audio_path,
            "prompt_lang": prompt_lang,
            "prompt_text": prompt_text,
            "text_split_method": text_split_method,
            "batch_size": batch_size,
            "media_type": media_type,
            "streaming_mode": False  # 非流式模式
        }

        try:
            print(f"tts.client: 请求 URL: {url}, 参数: {params}")
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.content  # 返回完整的音频数据
            else:
                return {"error": f"请求失败，状态码: {response.status_code}", "details": response.text}
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}

    def synthesize_stream(self, text: str, text_lang: str, ref_audio_path: str, prompt_lang: str, prompt_text: str, text_split_method: str, batch_size: int, media_type: str, streaming_mode: bool):
        """
        调用 TTS 后端进行语音合成（流式）
        """
        if not self.server_url:
            raise ValueError("TTS 后端 URL 未设置")

        url = f"{self.server_url}/tts"
        params = {
            "text": text,
            "text_lang": text_lang,
            "ref_audio_path": ref_audio_path,
            "prompt_lang": prompt_lang,
            "prompt_text": prompt_text,
            "text_split_method": text_split_method,
            "batch_size": batch_size,
            "media_type": media_type,
            "streaming_mode": True  # 强制使用流式模式
        }

        try:
            print(f"tts.client: 请求 URL: {url}, 参数: {params}")
            with requests.get(url, params=params, stream=True) as response:
                if response.status_code == 200:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            yield chunk
                else:
                    yield {"error": f"请求失败，状态码: {response.status_code}", "details": response.text}
        except Exception as e:
            yield {"error": f"请求失败: {str(e)}"}

# 测试用 main 函数
if __name__ == "__main__":
    import time
    # 初始化客户端
    client = TTSClient(server_url="http://183.175.12.68:9880")

    # 测试非流式合成
    print("\n=== 测试非流式合成 ===")
    result = client.synthesize(
        text="先帝创业未半而中道崩殂，今天下三分，益州疲弊，此诚危急存亡之秋也。",
        text_lang="zh",
        ref_audio_path="/data/qinxu/GPT-SoVITS/output/slicer_opt/录音 3.wav_0000005440_0000127680.wav",
        prompt_lang="zh",
        prompt_text="也许过大的目标会导致逻辑上的越界",
        text_split_method="cut5",
        batch_size=1,
        media_type="wav",
        streaming_mode=False
    )
    if isinstance(result, bytes):
        print(f"非流式合成成功:")
        print(f"音频大小: {len(result)} 字节")
        print(f"音频内容前100字节: {result[:100]}")
    else:
        print(f"非流式合成失败: {result}")

    print("\n等待5秒后测试流式合成...")
    time.sleep(5)

    # 测试流式合成
    print("\n=== 测试流式合成 ===")
    total_size = 0
    chunk_count = 0
    stream_result = client.synthesize_stream(
        text="先帝创业未半而中道崩殂，今天下三分，益州疲弊，此诚危急存亡之秋也。",
        text_lang="zh",
        ref_audio_path="/data/qinxu/GPT-SoVITS/output/slicer_opt/录音 3.wav_0000005440_0000127680.wav",
        prompt_lang="zh",
        prompt_text="也许过大的目标会导致逻辑上的越界",
        text_split_method="cut5",
        batch_size=1,
        media_type="wav",
        streaming_mode=True
    )
    
    print("开始接收流式数据...")
    for chunk in stream_result:
        if isinstance(chunk, bytes):
            chunk_count += 1
            chunk_size = len(chunk)
            total_size += chunk_size
            print(f"第 {chunk_count} 个数据块:")
            print(f"- 大小: {chunk_size} 字节")
            print(f"- 内容前50字节: {chunk[:50]}")
        else:
            print(f"流式合成失败: {chunk}")
            break
    
    print(f"\n流式合成完成:")
    print(f"- 总数据块数: {chunk_count}")
    print(f"- 总数据大小: {total_size} 字节")
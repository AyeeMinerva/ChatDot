import asyncio
import types
from tts.client import TTSClient
from tts.settings import TTSSettings
from tts.persistence import TTSPersistence
from tts.audio_player import AudioPlayer
from tts.audio_player import player
import time

class TTSService:
    """
    TTS 服务类
    """
    def __init__(self):
        self._initialized = False
        self.settings = TTSSettings()
        self.persistence = TTSPersistence()
        self.client = None

    def initialize(self):
        """
        初始化服务
        """
        if self._initialized:
            return

        # 加载持久化配置
        config = self.persistence.load_config()
        if config:
            for key, value in config.items():
                self.settings.update_setting(key, value)

        # 检查是否需要初始化
        if not self.settings.get_setting("initialize"):
            print("TTS 初始化被禁用，跳过初始化")
            return

        # 设置客户端 URL
        url = self.settings.get_setting("url")
        if url:
            self.client = TTSClient(server_url=url)
        else:
            print("警告: TTS URL 未设置，无法初始化客户端")

        self._initialized = True
        
    def is_tts_enabled(self) -> bool:
        """
        检查 TTS 是否启用
        :return: bool
        """
        return self.settings.get_setting("initialize")

    def text_to_speech(self, text: str):
        """
        调用 TTS 客户端进行语音合成
        :param text: 文本内容
        :return: 音频数据（字节流）或生成器
        """
        if not self.settings.get_setting("initialize"):
            raise RuntimeError("TTS 未启用")

        if not self.client:
            raise RuntimeError("TTS 客户端未初始化")

        # 从设置中获取参数
        text_lang = self.settings.get_setting("text_lang")
        ref_audio_path = self.settings.get_setting("ref_audio_path")
        prompt_lang = self.settings.get_setting("prompt_lang")
        prompt_text = self.settings.get_setting("prompt_text")
        text_split_method = self.settings.get_setting("text_split_method")
        batch_size = self.settings.get_setting("batch_size")
        media_type = self.settings.get_setting("media_type")
        streaming_mode = self.settings.get_setting("streaming_mode")

        if not text_lang or not ref_audio_path or not prompt_lang or not prompt_text:
            raise ValueError("TTS 设置不完整，请检查配置")

        if streaming_mode:
            #print("使用流式合成")
            return self.client.synthesize_stream(
                text=text,
                text_lang=text_lang,
                ref_audio_path=ref_audio_path,
                prompt_lang=prompt_lang,
                prompt_text=prompt_text,
                text_split_method=text_split_method,
                batch_size=batch_size,
                media_type=media_type,
                streaming_mode=True
            )
        else:
            #print("使用非流式合成")
            return self.client.synthesize(
                text=text,
                text_lang=text_lang,
                ref_audio_path=ref_audio_path,
                prompt_lang=prompt_lang,
                prompt_text=prompt_text,
                text_split_method=text_split_method,
                batch_size=batch_size,
                media_type=media_type,
                streaming_mode=False
            )

    def play_text_to_speech(self, text: str):
        """
        播放合成的语音
        """
        print("开始播放合成语音...")
        result = self.text_to_speech(text)
        
        if not isinstance(result, (bytes, types.GeneratorType)):
            print(f"合成失败: {result}")
            return

        try:
            # 停止任何正在播放的音频
            player.stop()
            
            # 重新启动播放器
            player.start()
            
            if isinstance(result, bytes):
                # 非流式模式：直接播放完整音频
                print(f"播放完整音频，大小: {len(result)} 字节")
                player.feed_data(result)
            else:
                # 流式模式：逐块处理
                chunk_count = 0
                total_size = 0
                for chunk in result:
                    if isinstance(chunk, bytes):
                        chunk_count += 1
                        chunk_size = len(chunk)
                        total_size += chunk_size
                        #print(f"处理第 {chunk_count} 个音频块，大小: {chunk_size} 字节")
                        player.feed_data(chunk)
                        # 添加小延迟，防止缓冲区溢出
                        time.sleep(0.01)
                    else:
                        print(f"处理音频块失败: {chunk}")
                        break
                print(f"流式处理完成，共处理 {chunk_count} 个音频块，总大小 {total_size} 字节")
        except Exception as e:
            print(f"播放音频时发生错误: {e}")

    def update_setting(self, key, value):
        """
        更新设置并保存
        """
        self.settings.update_setting(key, value)
        if key == "url" and self.client:
            #若之前没有url,则初始化客户端
            if not self.client:
                self.client = TTSClient(value)
            else:
                self.client.set_server_url(value)
        self.save_config()

    def save_config(self):
        """
        保存当前配置
        """
        config = {
            "url": self.settings.get_setting("url"),
            "initialize": self.settings.get_setting("initialize"),
            "streaming_mode": self.settings.get_setting("streaming_mode")
        }
        self.persistence.save_config(config)

    def shutdown(self):
        """
        关闭服务
        """
        print("TTSService 已关闭")


if __name__ == "__main__":

    print("=== 测试 TTSService ===")
    
    try:
        # 初始化服务
        print("\n1. 初始化服务")
        tts_service = TTSService()
        tts_service.initialize()
        tts_service.update_setting("url", "http://183.175.12.68:9880")
        
        # 测试流式模式
        #print("\n2. 测试流式模式")
        #tts_service.update_setting("streaming_mode", True)
        test_text = "先帝创业未半而中道崩殂，今天下三分，益州疲弊，此诚危急存亡之秋也。"
        print(f"测试文本: {test_text}")
        
        tts_service.play_text_to_speech(test_text)
        
        # 等待流式播放完成
        print("\n等待10秒后测试非流式模式...")
        time.sleep(20)
        
        # 测试非流式模式
        print("\n3. 测试非流式模式")
        tts_service.update_setting("streaming_mode", False)
        print(f"测试文本: {test_text}")
        tts_service.play_text_to_speech(test_text)
        
        # 等待非流式播放完成
        print("\n等待10秒后结束测试...")
        time.sleep(20)
        
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
    finally:
        print("\n=== 测试结束 ===")
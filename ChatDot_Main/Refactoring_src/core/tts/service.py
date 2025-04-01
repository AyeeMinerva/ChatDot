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
    
    def switch_gpt_model(self, weights_path: str):
        """
        切换GPT模型
        
        Args:
            weights_path: GPT模型权重文件路径
        
        Returns:
            成功返回True，失败返回错误信息
        """
        if not self.client:
            return {"error": "TTS客户端未初始化"}
            
        try:
            result = self.client.set_gpt_weights(weights_path)
            if result == "success":
                print(f"成功切换GPT模型: {weights_path}")
                return True
            return {"error": f"切换GPT模型失败: {result}"}
        except Exception as e:
            return {"error": f"切换GPT模型时发生错误: {str(e)}"}

    def switch_sovits_model(self, weights_path: str):
        """
        切换Sovits模型
        
        Args:
            weights_path: Sovits模型权重文件路径
        
        Returns:
            成功返回True，失败返回错误信息
        """
        if not self.client:
            return {"error": "TTS客户端未初始化"}
            
        try:
            result = self.client.set_sovits_weights(weights_path)
            if result == "success":
                print(f"成功切换Sovits模型: {weights_path}")
                return True
            return {"error": f"切换Sovits模型失败: {result}"}
        except Exception as e:
            return {"error": f"切换Sovits模型时发生错误: {str(e)}"}
        
    def switch_preset(self, preset_id):
        """
        切换预设，包括切换模型和更新设置
        
        Args:
            preset_id: 预设ID
            
        Returns:
            成功返回True，失败返回包含错误信息的字典
        """
        preset = self.settings.get_preset(preset_id)
        if not preset:
            return {"error": "预设不存在"}

        # 1. 切换 GPT 模型
        gpt_result = self.switch_gpt_model(preset.get("gpt_weights_path"))
        if isinstance(gpt_result, dict) and "error" in gpt_result:
            return gpt_result

        # 2. 切换 Sovits 模型
        sovits_result = self.switch_sovits_model(preset.get("sovits_weights_path"))
        if isinstance(sovits_result, dict) and "error" in sovits_result:
            return sovits_result

        # 3. 更新设置
        if not self.settings.switch_preset(preset_id):
            return {"error": "更新预设设置失败"}

        return True

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

    def play_text_to_speech(self, text: str, force_play=True):
        """
        播放合成的语音
        """
        print("开始播放合成语音...")
        result = self.text_to_speech(text)
        
        if not isinstance(result, (bytes, types.GeneratorType)):
            print(f"合成失败: {result}")
            return

        try:
            if force_play:
                # 强制停止任何正在播放的音频
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
            
    def realtime_play_text_to_speech(self, text_chunk=None, force_process=False):
        """
        实时文本转语音处理，将文本块收集到缓冲区，在遇到标点符号时进行句级TTS
        
        Args:
            text_chunk: 新的文本块，None表示不添加新文本
            force_process: 是否强制处理缓冲区中的所有文本，不论是否遇到标点
        """
        # 第一次调用时初始化缓冲区
        if not hasattr(self, '_text_buffer'):
            self._text_buffer = ""
        
        # 添加新文本到缓冲区
        if text_chunk:
            self._text_buffer += text_chunk
        
        # 定义句子结束标点
        sentence_end_punctuation = ["。", "！", "？", ".", "!", "?", "\n"]
        
        # 如果强制处理或缓冲区为空，则不需要继续
        if not self._text_buffer:
            return
        
        # 检查是否需要处理缓冲区
        if force_process:
            # 强制处理所有剩余文本
            if self._text_buffer.strip():
                print(f"强制处理剩余文本: {self._text_buffer}")
                self.play_text_to_speech(self._text_buffer, force_play=False)
                self._text_buffer = ""
            return
        
        # 查找句子结束标点
        process_index = -1
        for punct in sentence_end_punctuation:
            pos = self._text_buffer.rfind(punct)
            if pos > process_index:
                process_index = pos
                
        # 如果找到标点，处理到该标点为止的文本
        if process_index >= 0:
            # 提取要处理的文本（包括标点）
            process_text = self._text_buffer[:process_index + 1]
            # 保留剩余文本在缓冲区
            self._text_buffer = self._text_buffer[process_index + 1:]
            
            if process_text.strip():
                print(f"处理句子: {process_text}")
                self.play_text_to_speech(process_text, force_play=False)
        
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
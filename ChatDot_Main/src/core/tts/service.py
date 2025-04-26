import asyncio
import types
from tts.client import TTSClient
from tts.settings import TTSSettings
from tts.persistence import TTSPersistence
from tts.audio_player import AudioPlayer
from tts.audio_player import player
import time
from typing import List, Dict, Optional
from global_managers.logger_manager import LoggerManager
from tts.tts_handle.manager import TTSHandleManager

class TTSService:
    """
    TTS 服务类
    """
    def __init__(self):
        self._initialized = False
        self.settings = TTSSettings()
        self.persistence = TTSPersistence()
        self.client = None
        
        # 初始化TTS处理器管理器
        self.handler_manager = TTSHandleManager()

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
            LoggerManager().get_logger().debug("TTS 初始化被禁用，跳过初始化")
            return

        # 设置客户端 URL
        url = self.settings.get_setting("url")
        if url:
            self.client = TTSClient(server_url=url)
        else:
            LoggerManager().get_logger().warning("警告: TTS URL 未设置，无法初始化客户端")

        self._initialized = True
        
    def is_tts_enabled(self) -> bool:
        """
        检查 TTS 是否启用
        :return: bool
        """
        return self.settings.get_setting("initialize")
    
    def is_playing(self):
        """
        检查是否当前有TTS音频在播放
        
        Returns:
            bool: 是否有音频在播放
        """
        #LoggerManager().get_logger().debug("检查是否有音频正在播放...")
        if hasattr(self, '_text_buffer') and self._text_buffer:
            return True  # 缓冲区有内容，视为正在播放
        return player.is_playing() if hasattr(player, 'is_playing') else False

    def stop_playing(self):
        """
        停止所有正在播放的TTS音频
        """
        # 清空缓冲区
        LoggerManager().get_logger().debug("停止播放音频，清空缓冲区")
        if hasattr(self, '_text_buffer'):
            self._text_buffer = ""
        if hasattr(self, '_processed_sentences'):
            self._processed_sentences.clear()
        # 停止播放器
        player.stop()
    
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
                LoggerManager().get_logger().debug(f"成功切换GPT模型: {weights_path}")
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
                LoggerManager().get_logger().debug(f"成功切换Sovits模型: {weights_path}")
                return True
            return {"error": f"切换Sovits模型失败: {result}"}
        except Exception as e:
            return {"error": f"切换Sovits模型时发生错误: {str(e)}"}
    
    #region 预设管理
    def get_preset(self, preset_id=None):
        """获取预设配置"""
        if preset_id is None:
            preset_id = self.settings.get_setting("current_preset")
        presets = self.settings.get_setting("presets")
        return presets.get(preset_id)

    def add_preset(self, preset_id: str, preset_data: dict) -> bool:
        """添加预设"""
        if not preset_id or not preset_data:
            return False
            
        presets = self.settings.get_setting("presets")
        if preset_id in presets:
            return False
            
        presets[preset_id] = preset_data
        self.update_setting("presets", presets)
        return True

    def remove_preset(self, preset_id: str) -> bool:
        """删除预设"""
        if preset_id == "default":
            return False
            
        presets = self.settings.get_setting("presets")
        if preset_id not in presets:
            return False
            
        del presets[preset_id]
        self.update_setting("presets", presets)
        return True

    def get_all_presets(self) -> dict:
        """获取所有预设"""
        return self.settings.get_setting("presets")

    def switch_preset(self, preset_id: str) -> bool | dict:
        """
        切换预设，包括切换模型和更新设置

        Args:
            preset_id: 预设ID

        Returns:
            成功返回True，失败返回包含错误信息的字典
        """
        if preset_id is None:
            return {"error": "预设ID不能为空"}
            
        presets = self.settings.get_setting("presets")
        preset = presets.get(preset_id)
        
        if not preset:
            return {"error": "预设不存在"}

        try:
            # 1. 切换 GPT 模型
            gpt_result = self.switch_gpt_model(preset.get("gpt_weights_path"))
            if isinstance(gpt_result, dict) and "error" in gpt_result:
                return gpt_result

            # 2. 切换 Sovits 模型
            sovits_result = self.switch_sovits_model(preset.get("sovits_weights_path"))
            if isinstance(sovits_result, dict) and "error" in sovits_result:
                return sovits_result

            # 3. 更新当前预设ID
            self.update_setting("current_preset", preset_id)
            
            # 4. 更新相关设置
            for key, value in preset.items():
                if key != "name":  # 跳过预设名称
                    self.update_setting(key, value)
                    
            return True
            
        except Exception as e:
            return {"error": f"切换预设时发生错误: {str(e)}"}
    #endregion

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
            raise ValueError(f"TTS 设置不完整，当前缺失的参数：{', '.join([param for param in ['text_lang', 'ref_audio_path', 'prompt_lang', 'prompt_text'] if not self.settings.get_setting(param)])}")
                             
        if streaming_mode:
            #LoggerManager().get_logger().debug("使用流式合成")
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
            #LoggerManager().get_logger().debug("使用非流式合成")
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
        LoggerManager().get_logger().debug("开始播放合成语音...")
        result = self.text_to_speech(text)
        
        if not isinstance(result, (bytes, types.GeneratorType)):
            LoggerManager().get_logger().debug(f"合成失败: {result}")
            return

        try:
            if force_play:
                # 强制停止任何正在播放的音频
                player.stop()
            
            # 重新启动播放器
            player.start()
            
            if isinstance(result, bytes):
                # 非流式模式：直接播放完整音频
                LoggerManager().get_logger().debug(f"播放完整音频，大小: {len(result)} 字节")
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
                        #LoggerManager().get_logger().debug(f"处理第 {chunk_count} 个音频块，大小: {chunk_size} 字节")
                        player.feed_data(chunk)
                        # 添加小延迟，防止缓冲区溢出
                        time.sleep(0.01)
                    else:
                        LoggerManager().get_logger().warning(f"处理音频块失败: {chunk}")
                        break
                LoggerManager().get_logger().debug(f"流式处理完成，共处理 {chunk_count} 个音频块，总大小 {total_size} 字节")
        except Exception as e:
            LoggerManager().get_logger().warning(f"播放音频时发生错误: {e}")
            
    def realtime_play_text_to_speech(self, text_chunk=None, force_process=False):
        """
        实时文本转语音处理，将文本块收集到缓冲区，根据当前处理器策略进行TTS
        
        Args:
            text_chunk: 新的文本块，None表示不添加新文本
            force_process: 是否强制处理缓冲区中的所有文本，不论是否遇到标点
        """
        # 第一次调用时初始化缓冲区
        if not hasattr(self, '_text_buffer'):
            self._text_buffer = ""
        
        # 获取当前处理器
        handler = self.handler_manager.get_current_handler()
        if not handler:
            # 降级到默认处理方式（旧的逻辑）
            self._legacy_realtime_play_text_to_speech(text_chunk, force_process)
            return
        
        # 使用处理器处理文本
        process_text, self._text_buffer = handler.process_text_chunk(
            text_chunk, 
            self._text_buffer,
            force_process
        )
        
        # 处理得到的文本
        if process_text and process_text.strip():
            LoggerManager().get_logger().debug(f"TTS处理器[{handler.__class__.__name__}]处理文本: {process_text}")
            self.play_text_to_speech(process_text, force_play=False)
            
    def _legacy_realtime_play_text_to_speech(self, text_chunk=None, force_process=False):
        """
        旧的实时文本转语音处理，作为备用方法
        """
        # 添加新文本到缓冲区
        if text_chunk:
            self._text_buffer += text_chunk
        
        # 定义句子结束标点
        sentence_end_punctuation = ["。", "！", "？", ".", "!", "?", "\n"]
        
        # 缓冲区为空直接返回
        if not self._text_buffer:
            return
        
        # 强制处理模式 - 用于处理最后剩余的文本
        if force_process:
            if self._text_buffer.strip():
                LoggerManager().get_logger().debug(f"强制处理剩余文本: {self._text_buffer}")
                self.play_text_to_speech(self._text_buffer, force_play=False)
                self._text_buffer = ""
            return
        
        # 寻找句子结束标点
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
                LoggerManager().get_logger().debug(f"处理句子: {process_text}")
                self.play_text_to_speech(process_text, force_play=False)
                
    #region TTS处理器管理
    def get_tts_handler(self) -> str:
        """获取当前TTS处理器ID"""
        handler = self.handler_manager.get_current_handler()
        if not handler:
            return "未设置"
        for name, handler_class in self.handler_manager.handlers.items():
            if isinstance(handler, handler_class):
                return name
        return "未知"

    def set_tts_handler(self, handler_id: str) -> bool:
        """设置TTS处理器"""
        return self.handler_manager.set_handler(handler_id)

    def get_available_tts_handlers(self) -> List[Dict]:
        """获取所有可用的TTS处理器"""
        return self.handler_manager.get_available_handlers()
    #endregion
        
    def update_setting(self, key, value):
        """
        更新设置并保存
        """
        self.settings.update_setting(key, value)
        self.save_config()
        
        # 初始化参数
        if key == "initialize":
            if value:
                self.initialize()
        
        # URL 相关设置
        elif key == "url":
            if not self.client:
                self.client = TTSClient(value)
            else:
                self.client.set_server_url(value)
        
        # 模型相关设置
        elif key == "gpt_model_path":
            self.client.set_gpt_weights(value)
        elif key == "sovits_model_path":
            self.client.set_sovits_weights(value)
        
        # TTS 处理器相关设置
        elif key == "tts_handler" and hasattr(self, "handler_manager"):
            self.handler_manager.set_handler(value)

    def save_config(self):
        """
        保存当前配置
        """
        config = {
            # 基础配置
            "url": self.settings.get_setting("url"),
            "initialize": self.settings.get_setting("initialize"), 
            
            # 合成参数
            "text_lang": self.settings.get_setting("text_lang"),
            "ref_audio_path": self.settings.get_setting("ref_audio_path"),
            "prompt_lang": self.settings.get_setting("prompt_lang"),
            "prompt_text": self.settings.get_setting("prompt_text"),
            "text_split_method": self.settings.get_setting("text_split_method"),
            "batch_size": self.settings.get_setting("batch_size"),
            "media_type": self.settings.get_setting("media_type"),
            "streaming_mode": self.settings.get_setting("streaming_mode"),
            
            # 模型配置
            "sovits_model_path": self.settings.get_setting("sovits_model_path"),
            "gpt_weights_path": self.settings.get_setting("gpt_weights_path"),
            
            # 预设配置
            "current_preset": self.settings.get_setting("current_preset"),
            "presets": self.settings.get_setting("presets"),
            
            # TTS处理器配置
            "tts_handler": self.get_tts_handler(),  # 添加当前TTS处理器
        }
        self.persistence.save_config(config)

    def shutdown(self):
        """
        关闭服务
        """
        self.stop_playing()
        self.save_config()
        LoggerManager().get_logger().debug("TTS服务已关闭")


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
from global_managers.settings_manager import SettingsManager

DEFAULT_TTS_SETTINGS = {
    "url": None,  # TTS 后端的 URL
    "initialize": True,  # 是否启用 TTS
    "text_lang": "zh",  # 文本语言，默认中文
    "ref_audio_path": "/data/qinxu/GPT-SoVITS/sample_audios/也许过大的目标会导致逻辑上的越界.wav",  # 默认参考音频路径
    "prompt_lang": "zh",  # 提示语言，默认中文
    "prompt_text": "也许过大的目标会导致逻辑上的越界",  # 默认提示文本
    "text_split_method": "cut5",  # 文本分割方法，默认 "cut5"
    "batch_size": 1,  # 批处理大小，默认 1
    "media_type": "wav",  # 返回音频的媒体类型，默认 "wav"
    "streaming_mode": True  # 是否启用流式响应，默认 True
}

class TTSSettings:
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.settings_manager.register_module("tts", DEFAULT_TTS_SETTINGS)

    def get_setting(self, key):
        """
        获取 TTS 的某个设置
        """
        return self.settings_manager.get_setting("tts", key)

    def update_setting(self, key, value):
        """
        更新设置并保存
        """
        self.settings_manager.update_setting("tts", key, value)
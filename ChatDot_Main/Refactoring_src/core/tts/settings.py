from global_managers.settings_manager import SettingsManager
from .preset import TTSPresetManager

DEFAULT_TTS_SETTINGS = {
    "url": None,
    "initialize": True,
    "text_lang": "zh",
    "ref_audio_path": "/data/qinxu/GPT-SoVITS/sample_audios/37_也许过大的目标会导致逻辑上的越界.wav",
    "prompt_lang": "zh",
    "prompt_text": "也许过大的目标会导致逻辑上的越界",
    "text_split_method": "cut5",
    "batch_size": 1,
    "media_type": "wav",
    "streaming_mode": True,
    "current_preset": "default"
}

class TTSSettings:
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.settings_manager.register_module("tts", DEFAULT_TTS_SETTINGS)
        self.preset_manager = TTSPresetManager()

    def get_setting(self, key):
        """获取 TTS 的某个设置"""
        return self.settings_manager.get_setting("tts", key)

    def update_setting(self, key, value):
        """更新设置并保存"""
        self.settings_manager.update_setting("tts", key, value)

    def get_preset(self, preset_id=None):
        """获取预设配置"""
        if preset_id is None:
            preset_id = self.get_setting("current_preset")
        return self.preset_manager.get_preset(preset_id)

    def switch_preset(self, preset_id):
        """
        切换预设配置（仅更新设置，不包括模型切换）
        """
        preset = self.get_preset(preset_id)
        if not preset:
            return False

        # 更新当前预设ID
        self.update_setting("current_preset", preset_id)
        
        # 更新相关设置
        self.update_setting("text_lang", preset.get("text_lang", "zh"))
        self.update_setting("ref_audio_path", preset.get("ref_audio_path"))
        self.update_setting("prompt_lang", preset.get("prompt_lang", "zh"))
        self.update_setting("prompt_text", preset.get("prompt_text"))
        
        return True

    def add_preset(self, preset_id, preset_data):
        """添加预设"""
        return self.preset_manager.add_preset(preset_id, preset_data)

    def remove_preset(self, preset_id):
        """删除预设"""
        return self.preset_manager.remove_preset(preset_id)

    def get_all_presets(self):
        """获取所有预设"""
        return self.preset_manager.get_all_presets()
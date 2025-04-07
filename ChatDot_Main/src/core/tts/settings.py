from global_managers.settings_manager import SettingsManager
from global_managers.logger_manager import LoggerManager
import warnings

DEFAULT_TTS_SETTINGS = {
    # 基础配置
    "url": None,  # TTS服务器URL
    "initialize": True,  # 是否启用TTS
    
    # 合成参数
    "text_lang": "zh",  
    "prompt_lang": "zh",
    "text_split_method": "cut5",
    "batch_size": 1,
    "media_type": "wav",
    "streaming_mode": True,
    
    # 模型配置
    "gpt_weights_path": None,
    "sovits_weights_path": None,
    
    # 语音参考 
    "ref_audio_path": None,
    "prompt_text": None,
    
    # 预设
    "current_preset": "default",
    "presets": {
        "default": {
            "name": "默认配置",
            "gpt_weights_path": "/data/qinxu/GPT-SoVITS/GPT_weights_v2/37_1-e15.ckpt",
            "sovits_weights_path": "/data/qinxu/GPT-SoVITS/SoVITS_weights_v2/37_1_e8_s216.pth",
            "ref_audio_path": "/data/qinxu/GPT-SoVITS/sample_audios/37_也许过大的目标会导致逻辑上的越界.wav",
            "prompt_text": "也许过大的目标会导致逻辑上的越界",
            "text_lang": "zh",
            "prompt_lang": "zh",
            "text_split_method": "cut5",
            "batch_size": 1,
            "media_type": "wav",
            "streaming_mode": True
        }
    }
}

class TTSSettings:
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.settings_manager.register_module("tts", DEFAULT_TTS_SETTINGS)

    def get_setting(self, key):
        """获取设置值"""
        return self.settings_manager.get_setting("tts", key)

    def update_setting(self, key, value):
        """更新设置值"""
        self.settings_manager.update_setting("tts", key, value)
        
    ###############################
    # 警告部分
    # 以下是已迁移到 TTSService 的方法，保留接口但给出警告
    def get_preset(self, preset_id=None):
        """获取预设配置"""
        warnings.warn(
            "预设管理功能已迁移至 TTSService，请使用 tts_service.get_preset() 方法",
            DeprecationWarning,
            stacklevel=2
        )
        raise NotImplementedError("此方法已迁移至 TTSService")

    def get_all_presets(self):
        """获取所有预设"""
        warnings.warn(
            "预设管理功能已迁移至 TTSService，请使用 tts_service.get_all_presets() 方法",
            DeprecationWarning,
            stacklevel=2
        )
        raise NotImplementedError("此方法已迁移至 TTSService")

    def add_preset(self, preset_id, preset_data):
        """添加预设"""
        warnings.warn(
            "预设管理功能已迁移至 TTSService，请使用 tts_service.add_preset() 方法",
            DeprecationWarning,
            stacklevel=2
        )
        raise NotImplementedError("此方法已迁移至 TTSService")

    def remove_preset(self, preset_id):
        """删除预设"""
        warnings.warn(
            "预设管理功能已迁移至 TTSService，请使用 tts_service.remove_preset() 方法",
            DeprecationWarning,
            stacklevel=2
        )
        raise NotImplementedError("此方法已迁移至 TTSService")

    def switch_preset(self, preset_id):
        """切换预设"""
        warnings.warn(
            "预设管理功能已迁移至 TTSService，请使用 tts_service.switch_preset() 方法",
            DeprecationWarning,
            stacklevel=2
        )
        raise NotImplementedError("此方法已迁移至 TTSService")
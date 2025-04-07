import os
import json
from pathlib import Path

class TTSPresetManager:
    def __init__(self, preset_file_path=None):
        if preset_file_path is None:
            preset_file_path = Path("ChatDot_Main/Refactoring_src/core/tts/config/tts_presets.json")
        
        self.preset_file_path = Path(preset_file_path)
        self.presets = self._load_presets()

    def _load_presets(self):
        """加载预设配置"""
        default_preset = {
            "default": {
                "name": "37",
                "ref_audio_path": "/data/qinxu/GPT-SoVITS/sample_audios/37_也许过大的目标会导致逻辑上的越界.wav",
                "prompt_text": "也许过大的目标会导致逻辑上的越界",
                "text_lang": "zh",
                "prompt_lang": "zh",
                "gpt_weights_path": "/data/qinxu/GPT-SoVITS/GPT_weights_v2/37_1-e15.ckpt",
                "sovits_weights_path": "/data/qinxu/GPT-SoVITS/SoVITS_weights_v2/37_1_e8_s216.pth"
            }
        }

        if not self.preset_file_path.exists():
            # 确保目录存在
            self.preset_file_path.parent.mkdir(parents=True, exist_ok=True)
            # 写入默认预设
            self.save_presets(default_preset)
            return default_preset

        try:
            with open(self.preset_file_path, 'r', encoding='utf-8') as f:
                presets = json.load(f)
                # 确保始终存在默认预设
                if "default" not in presets:
                    presets["default"] = default_preset["default"]
                return presets
        except Exception as e:
            print(f"加载预设文件失败: {e}")
            return default_preset

    def save_presets(self, presets):
        """保存预设配置"""
        try:
            with open(self.preset_file_path, 'w', encoding='utf-8') as f:
                json.dump(presets, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存预设文件失败: {e}")
            return False

    def get_preset(self, preset_id):
        """获取指定预设"""
        return self.presets.get(preset_id)

    def add_preset(self, preset_id, preset_data):
        """添加新预设"""
        if preset_id in self.presets:
            return False
        self.presets[preset_id] = preset_data
        return self.save_presets(self.presets)

    def remove_preset(self, preset_id):
        """删除预设"""
        if preset_id == "default":
            return False
        if preset_id in self.presets:
            del self.presets[preset_id]
            return self.save_presets(self.presets)
        return False

    def get_all_presets(self):
        """获取所有预设"""
        return self.presets
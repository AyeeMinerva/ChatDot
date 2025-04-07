from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QCheckBox, QComboBox, QLineEdit, QPushButton,
                            QGroupBox, QFormLayout, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
import os
import json
import subprocess
import sys

class VoiceSettingsPage(QWidget):
    """语音设置页面，包括TTS和STT设置"""
    settings_changed = pyqtSignal()
    
    def __init__(self, service_manager):
        super().__init__()
        self.service_manager = service_manager
        self.tts_service = service_manager.get_service("tts_service")
        self.stt_service = service_manager.get_service("stt_service")
        
        # 设置配置文件路径
        self.config_dir = os.path.join(os.path.expanduser("~"), ".chatdot")
        self.voice_config_path = os.path.join(self.config_dir, "voice_settings.json")
        
        # 敏感配置备份目录
        self.backup_dir = os.path.join(self.config_dir, "secrets_backup")
        
        # 确保配置目录存在
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # 确保备份目录存在
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        # 设置工具脚本路径
        self.sync_tool_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                          "utils", "sync_secret_files_tools", "sync_secrets.py")
        self.restore_tool_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                             "utils", "sync_secret_files_tools", "restore_secrets.py")
        
        self.initUI()
        self.load_settings_from_file()  # 从文件加载设置
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # TTS设置部分
        tts_group = QGroupBox("文本转语音 (TTS) 设置")
        tts_layout = QVBoxLayout()
        
        # TTS启用选项
        self.tts_enabled = QCheckBox("启用TTS功能")
        self.tts_enabled.toggled.connect(self.on_settings_changed)
        tts_layout.addWidget(self.tts_enabled)
        
        # TTS服务器设置
        tts_form = QFormLayout()
        self.tts_url = QLineEdit()
        self.tts_url.textChanged.connect(self.on_settings_changed)
        tts_form.addRow("TTS服务器URL:", self.tts_url)
        
        # TTS预设选择
        self.tts_preset_combo = QComboBox()
        self.tts_preset_combo.currentIndexChanged.connect(self.on_settings_changed)
        tts_form.addRow("角色预设:", self.tts_preset_combo)
        
        # 测试TTS按钮
        self.test_tts_btn = QPushButton("测试TTS")
        self.test_tts_btn.clicked.connect(self.test_tts)
        tts_form.addRow("", self.test_tts_btn)
        
        tts_layout.addLayout(tts_form)
        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group)
        
        # STT设置部分
        stt_group = QGroupBox("语音转文本 (STT) 设置")
        stt_layout = QVBoxLayout()
        
        # STT启用选项
        self.stt_enabled = QCheckBox("启用STT功能")
        self.stt_enabled.toggled.connect(self.on_settings_changed)
        stt_layout.addWidget(self.stt_enabled)
        
        # STT服务器设置
        stt_form = QFormLayout()
        
        # 服务器类型选择
        self.stt_server_type = QComboBox()
        self.stt_server_type.addItems(["本地服务器", "远程服务器"])
        self.stt_server_type.currentIndexChanged.connect(self.on_stt_server_type_changed)
        stt_form.addRow("服务器类型:", self.stt_server_type)
        
        # 服务器地址
        self.stt_host = QLineEdit()
        self.stt_host.textChanged.connect(self.on_settings_changed)
        stt_form.addRow("服务器地址:", self.stt_host)
        
        # 服务器端口
        self.stt_port = QLineEdit()
        self.stt_port.textChanged.connect(self.on_settings_changed)
        stt_form.addRow("服务器端口:", self.stt_port)
        
        # 自动启动服务器
        self.stt_auto_start = QCheckBox("自动启动本地服务器")
        self.stt_auto_start.toggled.connect(self.on_settings_changed)
        stt_form.addRow("", self.stt_auto_start)
        
        # 测试STT按钮
        self.test_stt_btn = QPushButton("测试STT")
        self.test_stt_btn.clicked.connect(self.test_stt)
        stt_form.addRow("", self.test_stt_btn)
        
        stt_layout.addLayout(stt_form)
        stt_group.setLayout(stt_layout)
        layout.addWidget(stt_group)
        
        # 配置同步按钮
        sync_layout = QHBoxLayout()
        
        self.backup_config_btn = QPushButton("备份敏感配置")
        self.backup_config_btn.clicked.connect(self.backup_config)
        sync_layout.addWidget(self.backup_config_btn)
        
        self.restore_config_btn = QPushButton("恢复敏感配置")
        self.restore_config_btn.clicked.connect(self.restore_config)
        sync_layout.addWidget(self.restore_config_btn)
        
        layout.addLayout(sync_layout)
        
        # 添加一些弹性空间
        layout.addStretch()
        
    def load_settings_from_file(self):
        """从文件加载设置，如果文件不存在则从服务加载默认设置"""
        try:
            if os.path.exists(self.voice_config_path):
                # 从文件加载设置
                with open(self.voice_config_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 加载TTS设置
                tts_settings = settings.get('tts', {})
                self.tts_enabled.setChecked(tts_settings.get('initialize', False))
                self.tts_url.setText(tts_settings.get('url', ''))
                
                # 加载TTS预设
                presets = self.tts_service.get_all_presets()
                self.tts_preset_combo.clear()
                for preset_id, preset_data in presets.items():
                    self.tts_preset_combo.addItem(f"{preset_data['name']} ({preset_id})", preset_id)
                
                # 设置当前预设
                current_preset_id = tts_settings.get('current_preset', '')
                for i in range(self.tts_preset_combo.count()):
                    if self.tts_preset_combo.itemData(i) == current_preset_id:
                        self.tts_preset_combo.setCurrentIndex(i)
                        break
                
                # 加载STT设置
                stt_settings = settings.get('stt', {})
                self.stt_enabled.setChecked(stt_settings.get('enabled', False))
                self.stt_host.setText(stt_settings.get('host', 'localhost'))
                self.stt_port.setText(str(stt_settings.get('port', 6008)))
                self.stt_auto_start.setChecked(stt_settings.get('auto_start_server', False))
                
                # 设置服务器类型
                use_local = stt_settings.get('use_local_server', True)
                self.stt_server_type.setCurrentIndex(0 if use_local else 1)
                self.on_stt_server_type_changed(0 if use_local else 1)  # 更新UI状态
                
                # 将加载的设置应用到服务中
                self.apply_settings_to_services(settings)
            else:
                # 如果文件不存在，从服务加载默认设置
                self.load_settings()
                # 并保存到文件
                self.save_settings_to_file()
                
        except Exception as e:
            QMessageBox.warning(self, "加载设置失败", f"无法从文件加载语音设置: {str(e)}")
            # 从服务加载默认设置
            self.load_settings()
    
    def apply_settings_to_services(self, settings):
        """将加载的设置应用到服务中"""
        try:
            # 应用TTS设置
            tts_settings = settings.get('tts', {})
            self.tts_service.update_setting("initialize", tts_settings.get('initialize', False))
            self.tts_service.update_setting("url", tts_settings.get('url', ''))
            
            # 应用TTS预设
            current_preset_id = tts_settings.get('current_preset', '')
            if current_preset_id:
                self.tts_service.switch_preset(current_preset_id)
            
            # 应用STT设置
            stt_settings = settings.get('stt', {})
            # 修正: 使用settings对象来更新设置，而不是直接调用update_setting
            self.stt_service.settings.update_setting("enabled", stt_settings.get('enabled', False))
            
            # 应用STT服务器设置
            use_local = stt_settings.get('use_local_server', True)
            self.stt_service.update_server_config(
                host=stt_settings.get('host', 'localhost'),
                port=stt_settings.get('port', 6008),
                use_local_server=use_local,
                auto_start_server=stt_settings.get('auto_start_server', False) if use_local else False
            )
        except Exception as e:
            QMessageBox.warning(self, "应用设置失败", f"无法将设置应用到服务: {str(e)}")
    
    def save_settings_to_file(self):
        """将当前设置保存到文件"""
        try:
            # 收集当前设置
            settings = {
                'tts': {
                    'initialize': self.tts_enabled.isChecked(),
                    'url': self.tts_url.text().strip(),
                    'current_preset': self.tts_preset_combo.currentData() if self.tts_preset_combo.currentData() else ''
                },
                'stt': {
                    'enabled': self.stt_enabled.isChecked(),
                    'host': self.stt_host.text().strip(),
                    'port': int(self.stt_port.text()) if self.stt_port.text().isdigit() else 6008,
                    'use_local_server': self.stt_server_type.currentIndex() == 0,
                    'auto_start_server': self.stt_auto_start.isChecked() if self.stt_server_type.currentIndex() == 0 else False
                }
            }
            
            # 创建一个名为SECRET_voice_settings.json的文件
            secret_path = os.path.join(os.path.dirname(self.voice_config_path), "SECRET_voice_settings.json")
            with open(secret_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
                
            # 同时保存到普通配置文件（不含敏感信息版本）
            # 这里可以移除一些敏感字段，如API密钥等
            with open(self.voice_config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            QMessageBox.warning(self, "保存设置失败", f"无法将设置保存到文件: {str(e)}")
    
    def backup_config(self):
        """备份敏感配置到安全位置"""
        try:
            # 确保设置已保存
            self.on_settings_changed()
            
            # 调用同步工具将敏感文件同步到备份目录
            python_executable = sys.executable
            command = [python_executable, self.sync_tool_path, self.config_dir, self.backup_dir]
            
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                QMessageBox.information(self, "备份成功", "敏感配置文件已成功备份")
            else:
                QMessageBox.warning(self, "备份失败", f"无法备份配置文件: {stderr}")
                
        except Exception as e:
            QMessageBox.critical(self, "备份错误", f"备份过程中发生错误: {str(e)}")
    
    def restore_config(self):
        """从备份位置恢复敏感配置"""
        try:
            # 检查备份目录是否存在
            if not os.path.exists(self.backup_dir) or not os.listdir(self.backup_dir):
                QMessageBox.warning(self, "恢复失败", "没有找到备份文件")
                return
            
            # 确认用户意图
            reply = QMessageBox.question(self, "确认恢复", 
                                       "恢复操作将覆盖当前的配置文件。是否继续？",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply != QMessageBox.Yes:
                return
            
            # 调用恢复工具从备份目录恢复文件
            python_executable = sys.executable
            command = [python_executable, self.restore_tool_path, self.backup_dir, self.config_dir]
            
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                QMessageBox.information(self, "恢复成功", "敏感配置文件已成功恢复")
                # 重新加载设置
                self.load_settings_from_file()
            else:
                QMessageBox.warning(self, "恢复失败", f"无法恢复配置文件: {stderr}")
                
        except Exception as e:
            QMessageBox.critical(self, "恢复错误", f"恢复过程中发生错误: {str(e)}")
    
    def load_settings(self):
        """从服务加载设置"""
        try:
            # 加载TTS设置
            self.tts_enabled.setChecked(self.tts_service.settings.get_setting("initialize"))
            self.tts_url.setText(self.tts_service.settings.get_setting("url"))
            
            # 加载TTS预设
            presets = self.tts_service.get_all_presets()
            self.tts_preset_combo.clear()
            for preset_id, preset_data in presets.items():
                self.tts_preset_combo.addItem(f"{preset_data['name']} ({preset_id})", preset_id)
            
            # 设置当前预设
            current_preset_id = self.tts_service.settings.get_setting("current_preset")
            for i in range(self.tts_preset_combo.count()):
                if self.tts_preset_combo.itemData(i) == current_preset_id:
                    self.tts_preset_combo.setCurrentIndex(i)
                    break
            
            # 加载STT设置
            self.stt_enabled.setChecked(self.stt_service.settings.get_setting("enabled"))
            self.stt_host.setText(self.stt_service.settings.get_setting("host"))
            self.stt_port.setText(str(self.stt_service.settings.get_setting("port")))
            self.stt_auto_start.setChecked(self.stt_service.settings.get_setting("auto_start_server"))
            
            # 设置服务器类型
            use_local = self.stt_service.settings.get_setting("use_local_server")
            self.stt_server_type.setCurrentIndex(0 if use_local else 1)
            self.on_stt_server_type_changed(0 if use_local else 1)  # 更新UI状态
            
        except Exception as e:
            QMessageBox.warning(self, "加载设置失败", f"无法加载语音设置: {str(e)}")
    
    def on_stt_server_type_changed(self, index):
        """STT服务器类型变更时的处理"""
        is_local = index == 0
        self.stt_host.setEnabled(not is_local)
        if is_local:
            self.stt_host.setText("localhost")
        self.stt_auto_start.setEnabled(is_local)
        self.on_settings_changed()
    
    def on_settings_changed(self):
        """设置变更时保存设置"""
        try:
            # 保存TTS设置
            self.tts_service.update_setting("initialize", self.tts_enabled.isChecked())
            self.tts_service.update_setting("url", self.tts_url.text().strip())
            
            # 保存TTS预设 - 只有在预设变更时才切换
            if self.tts_preset_combo.currentData():
                current_preset_id = self.tts_preset_combo.currentData()
                current_service_preset = self.tts_service.settings.get_setting("current_preset")
                
                # 只有当预设ID不同时才切换
                if current_preset_id != current_service_preset:
                    self.tts_service.switch_preset(current_preset_id)
            
            # 保存STT设置
            self.stt_service.settings.update_setting("enabled", self.stt_enabled.isChecked())
            
            # 保存STT服务器设置
            is_local = self.stt_server_type.currentIndex() == 0
            self.stt_service.update_server_config(
                host="localhost" if is_local else self.stt_host.text().strip(),
                port=int(self.stt_port.text()) if self.stt_port.text().isdigit() else 6008,
                use_local_server=is_local,
                auto_start_server=self.stt_auto_start.isChecked() if is_local else False
            )
            
            # 保存到文件
            self.save_settings_to_file()
            
            # 发送设置已更改信号
            self.settings_changed.emit()
            
        except Exception as e:
            QMessageBox.warning(self, "保存设置失败", f"无法保存语音设置: {str(e)}")
    
    def test_tts(self):
        """测试TTS功能"""
        if not self.tts_enabled.isChecked():
            QMessageBox.warning(self, "TTS未启用", "请先启用TTS功能")
            return
            
        from PyQt5.QtWidgets import QInputDialog
        
        test_text, ok = QInputDialog.getText(self, "TTS测试", "请输入要合成的文本:", 
                                            text="这是一个TTS测试")
        if ok and test_text:
            try:
                self.tts_service.play_text_to_speech(test_text)
                QMessageBox.information(self, "TTS测试", "TTS测试请求已发送，请听取语音输出")
            except Exception as e:
                QMessageBox.critical(self, "TTS测试失败", f"测试过程中出错: {str(e)}")
    
    def test_stt(self):
        """测试STT功能"""
        # 测试前保存当前设置
        self.on_settings_changed()
        
        if not self.stt_enabled.isChecked():
            QMessageBox.warning(self, "STT未启用", "请先启用STT功能")
            return
            
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        import asyncio
        
        # 创建一个测试对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("STT测试")
        layout = QVBoxLayout(dialog)
        
        status_label = QLabel("正在初始化STT服务...", dialog)
        result_label = QLabel("识别结果将显示在这里", dialog)
        stop_button = QPushButton("停止测试", dialog)
        
        layout.addWidget(status_label)
        layout.addWidget(result_label)
        layout.addWidget(stop_button)
        
        dialog.setLayout(layout)
        dialog.resize(400, 200)
        
        # STT测试函数
        async def run_stt_test():
            try:
                # 初始化STT
                if not await self.stt_service.initialize_async():
                    status_label.setText("STT服务初始化失败")
                    return
                
                status_label.setText("请开始说话...")
                
                # 添加回调
                def on_speech_recognized(text):
                    result_label.setText(f"识别结果: {text}")
                
                self.stt_service.segment_callbacks = []  # 清除现有回调
                self.stt_service.add_segment_callback(on_speech_recognized)
                
                # 启动识别
                if not await self.stt_service.start_recognition_async():
                    status_label.setText("启动语音识别失败")
                    return
                
                # 等待用户点击停止
                while not stop_pressed[0]:
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                status_label.setText(f"测试过程中出错: {str(e)}")
            finally:
                # 停止识别并关闭
                try:
                    await self.stt_service.stop_recognition_async()
                    await self.stt_service.shutdown_async()
                    status_label.setText("STT测试已停止")
                except Exception as e:
                    status_label.setText(f"关闭服务时出错: {str(e)}")
        
        # 设置停止按钮
        stop_pressed = [False]
        
        def on_stop():
            stop_pressed[0] = True
            stop_button.setEnabled(False)
            stop_button.setText("正在停止...")
        
        stop_button.clicked.connect(on_stop)
        
        # 启动测试
        def start_test():
            asyncio.run(run_stt_test())
            dialog.accept()
        
        import threading
        threading.Thread(target=start_test).start()
        
        # 显示对话框
        dialog.exec_()
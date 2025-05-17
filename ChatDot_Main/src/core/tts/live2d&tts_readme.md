# 音频管线（VB-Audio Virtual Cable）安装与配置说明

本项目支持通过“音频管线”方式，将系统音频输出作为输入设备采集，实现“声卡内录”或“立体声混音”效果。推荐使用 [VB-Audio Virtual Cable](https://www.vb-audio.com/Cable/index.htm) 工具，适用于 Windows 系统。

---

## 安装步骤

1. **下载驱动**
   - 访问 [VB-Audio Virtual Cable 官网](https://www.vb-audio.com/Cable/index.htm)。
   - 点击页面中的下载链接，解压缩下载的压缩包。

2. **安装驱动**
   - 以管理员身份运行 `VBCable_Setup_x64.exe`（64位系统）或 `VBCable_Setup.exe`（32位系统）。
   - 点击“Install Driver”按钮，等待安装完成。
   - 安装完成后，建议重启电脑。

3. **配置音频设备**
   - 打开“控制面板” → “声音” → “播放”标签，将“CABLE Input”设置为默认播放设备（可选）。
   - 打开“录制”标签，确认出现了“CABLE Output”设备。
   - 需要采集系统声音时，在程序中选择“CABLE Output”作为输入设备即可。

---

## 在 Python 中选择音频管线设备

你可以用如下代码枚举所有音频输入设备，找到“CABLE Output”的编号：

```python
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(i, info['name'])
```

然后在音频采集代码audio_player.py中，将输入设备 index 设置为“CABLE Output”对应的编号。

---

## 常见问题

- 如果未出现“CABLE Input”或“CABLE Output”，请确认驱动已正确安装，并尝试重启电脑。
- 若需同时监听和采集系统声音，可在“播放”设备中将“CABLE Input”设为默认，然后用耳机/音箱监听“CABLE Output”或使用“侦听此设备”功能。

---

## 参考链接

- [VB-Audio Virtual Cable 官方网站](https://www.vb-audio.com/Cable/index.htm)
- [官方安装说明（英文）](https://vb-audio.com/Cable/Manuals/Cable_UserManual.pdf)
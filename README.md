
![ChatDot](https://socialify.git.ci/AyeeMinerva/ChatDot/image?description=1&font=Inter&forks=1&issues=1&language=1&name=1&owner=1&pattern=Solid&pulls=1&stargazers=1&theme=Auto)

## 💡 Introduction | 简介

ChatDot is an innovative desktop floating chat assistant that provides instant access to AI conversations through OpenAI-compatible LLM APIs. Through [SillyTavern-Extension-ChatBridge](https://github.com/AyeeMinerva/SillyTavern-Extension-ChatBridge), it can seamlessly connect to SillyTavern, unlocking powerful character interaction capabilities.

ChatDot 是一个创新的桌面悬浮窗聊天助手，让你随时快速访问 AI 对话功能，支持 OpenAI 格式的标准 LLM API。同时还可以通过 SillyTavern-Extension-ChatBridge 连接到 SillyTavern，使用其强大的角色扮演功能。

## ✨ Features | 特色功能

### Elegant Interface | 优雅界面
- **Floating Ball Design | 悬浮球设计**
  - Drag anywhere | 随处可拖拽
  - Never block other windows | 永不遮挡
  - Sleek frosted glass effect | 优雅的磨砂玻璃效果

### Core Capabilities | 核心功能
- **Advanced Chat Features | 对话增强**
  - Streaming/non-streaming responses | 流式/非流式响应
  - Chat history management | 历史记录管理
  - API key rotation | 多 API 轮询
  - Message retry & alternatives | 消息重试与候选

### SillyTavern Integration | ST 集成
- **Seamless Connection | 无缝连接**
  - Dedicated ChatBridge extension support | 专用 ChatBridge 拓展支持
  - Access to character presets | 访问角色预设
  - Shared conversation context | 共享对话上下文
  - Advanced roleplay features | 高级角色扮演功能

## 🚀 Quick Start | 快速开始

```bash
# Clone the repository | 克隆仓库
git clone https://github.com/yourusername/ChatDot.git
cd ChatDot

# Install dependencies | 安装依赖
pip install -r requirements.txt

# Run the application | 运行程序
python src/main.py
```

## ⚙️ SillyTavern Integration Setup | ST 集成配置

1. Install and Launch SillyTavern | 安装并启动 SillyTavern
   - Follow the installation guide at [SillyTavern](https://github.com/SillyTavern/SillyTavern)
   - 参照 SillyTavern 官方仓库的安装指南进行安装

2. Install ChatBridge Extension | 安装 ChatBridge 拓展
   - Navigate to "Extensions" tab in ST settings
   - Install [ChatBridge](https://github.com/AyeeMinerva/SillyTavern-Extension-ChatBridge)
   - Restart ST to activate the extension
   
   - 在 ST 设置中找到 "Extensions" 标签页
   - 安装 ChatBridge 拓展
   - 重启 ST 使拓展生效

3. Start API Forwarding Service | 启动 API 转发服务
   ```bash
   # Navigate to extension directory | 进入拓展目录
   cd extensions/SillyTavern-Extension-ChatBridge
   
   # Run the API forwarding script | 运行 API 转发脚本
   python ChatBridge_APIHijackForwarder.py
   ```
   The script will display the User API server address (typically `http://localhost:5001/api/chat`)
   脚本将显示用户 API 服务器地址（通常为 `http://localhost:5001/api/chat`）

4. Configure ChatDot | 配置 ChatDot
   - Open ChatDot settings | 打开 ChatDot 设置
   - Enter the User API server address in "API Base URL" | 在 "API Base URL" 中填入用户 API 服务器地址

> Note | 注意：
> Please ensure both SillyTavern and ChatBridge_APIHijackForwarder.py remain running while using ChatDot.
> 请确保 SillyTavern 和 ChatBridge_APIHijackForwarder.py 在使用 ChatDot 期间保持运行状态。

## 📦 System Requirements | 系统要求

- Python 3.12
- PyQt5
- OpenAI SDK
- ...

## 📝 License | 许可证

GNU Affero General Public License v3.0

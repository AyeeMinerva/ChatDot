import asyncio
from live2d.client import Live2DClient
from live2d.settings import Live2DSettings
from live2d.persistence import Live2DPersistence

class Live2DService:
    """
    Live2D 服务类
    使用异步方式调用 Live2DClient 的功能，但提供同步接口
    """
    def __init__(self):
        self._initialized = False  # 初始化标记
        self.settings = Live2DSettings()
        self.persistence = Live2DPersistence()
        self.client = None  # 延迟初始化

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
            print("Live2D 初始化被禁用，跳过初始化")
            return

        # 设置客户端 URL 和情感分析状态
        url = self.settings.get_setting("url")
        enable_emotion = self.settings.get_setting("initialize")
        self.client = Live2DClient(server_url=url, enable_emotion=enable_emotion)

        if url:
            self.client.set_server_url(url)
        else:
            print("警告: Live2D URL 未设置，无法初始化客户端")

        self._initialized = True
        
    def is_live2d_enabled(self) -> bool:
        """
        检查 Live2D 是否启用
        :return: 如果启用返回 True，否则返回 False
        """
        return self.settings.get_setting("initialize")

    def set_server_url(self, server_url: str):
        """
        设置 Live2D 后端的服务器地址
        :param server_url: Live2D 后端的服务器地址
        """
        self.client.set_server_url(server_url)
        self.settings.update_setting("url", server_url)
        self.persistence.save_config({
            "url": server_url,
            "initialize": self.settings.get_setting("initialize")
        })

    async def _text_to_live2d_async(self, text: str):
        """
        异步处理文本并调用 Live2DClient 的 text_to_live2d 方法
        :param text: 输入的文本
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.client.text_to_live2d, text)

    def text_to_live2d(self, text: str):
        """
        此方法不会阻塞主线程
        同步处理文本并调用 Live2DClient 的 text_to_live2d 方法
        :param text: 输入的文本
        """
        if not self.settings.get_setting("initialize"):
            print("Live2D 未初始化，无法处理请求")
            return

        url = self.settings.get_setting("url")
        if not url:
            print("警告: Live2D URL 未设置，无法处理请求")
            return

        asyncio.run(self._text_to_live2d_async(text))

    def save_config(self):
        """
        保存当前配置
        """
        config = {
            "url": self.settings.get_setting("url"),
            "initialize": self.settings.get_setting("initialize")
        }
        self.persistence.save_config(config)

    def update_setting(self, key, value):
        """
        更新设置并保存
        """
        self.settings.update_setting(key, value)
        if key == "url":
            self.client.set_server_url(value)
        elif key == "initialize":
            if value:  # 如果启用
                print("正在启用 Live2D 服务...")
                self.initialize()
            else:  # 如果禁用
                print("正在禁用 Live2D 服务...")
                self.client = None  # 清理客户端实例
                self._initialized = False
        self.save_config()

    def shutdown(self):
        """
        关闭服务（可选）
        """
        print("Live2DService 已关闭")
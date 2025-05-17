import requests
from global_managers.logger_manager import LoggerManager

class Live2DAdapter:
    def __init__(self, server_url: str = None, enable_emotion: bool = True):
        """
        初始化 Live2D 客户端
        :param server_url: Live2D 后端的服务器地址（可选）
        :param enable_emotion: 是否启用情感分析
        """
        self.server_url = server_url

    def set_server_url(self, server_url: str):
        """
        设置 Live2D 后端的服务器地址
        :param server_url: Live2D 后端的服务器地址
        """
        self.server_url = server_url

    def text_to_live2d(self, text: str):
        """
        接收文本并发送到 Live2D 后端
        :param text: 输入的文本
        """
        if not self.server_url:
            LoggerManager().get_logger().warning("警告: Live2D 后端 URL 未设置，无法处理请求")
            return

        try:
            #直接发送给后端

            # 构造请求数据
            payload = {"chunk": text}
            LoggerManager().get_logger().debug(f"发送数据到 Live2D 后端: {payload}")

            # 发送 POST 请求到 Live2D 后端
            response = requests.post(self.server_url, json=payload)

            # 检查响应状态
            if response.status_code == 200:
                LoggerManager().get_logger().debug("成功发送数据到 Live2D 后端")
            else:
                LoggerManager().get_logger().warning(f"发送失败，状态码: {response.status_code}, 响应: {response.text}")
        except Exception as e:
            LoggerManager().get_logger().warning(f"发送数据时发生错误: {e}")

# 示例用法
if __name__ == "__main__":
    # 初始化 Live2D 客户端，指定后端地址
    live2d_adapter = Live2DAdapter("http://localhost:9000")

    while True:
        # 输入文本
        text = input("请输入文本: ")
        if text.lower() == "exit":
            print("退出程序")
            break

        # 分析情感并发送到 Live2D 后端
        live2d_adapter.text_to_live2d(text)
import requests

def test_live2d_backend(server_url: str, emotion: str):
    """
    测试 Live2D 后端是否正常工作
    :param server_url: Live2D 后端的服务器地址
    :param emotion: 要发送的情感数据
    """
    try:
        # 构造请求数据
        payload = {"emotion": emotion}  # 确保字段名与后端的 AiCommand 类一致
        headers = {"Content-Type": "application/json"}  # 设置请求头
        print(f"测试发送数据到 Live2D 后端: {payload}")

        # 发送 POST 请求到 Live2D 后端
        response = requests.post(server_url, json=payload, headers=headers)

        # 检查响应状态
        if response.status_code == 200:
            print("后端正常工作，响应内容:")
            print(response.text)
        else:
            print(f"后端返回错误，状态码: {response.status_code}, 响应: {response.text}")
    except Exception as e:
        print(f"测试时发生错误: {e}")

if __name__ == "__main__":
    # 设置 Live2D 后端地址
    server_url = "http://localhost:9000"  # 确保端口号正确

    # 测试情感数据
    test_emotions = ["happy", "sad", "angry", "neutral"]

    for emotion in test_emotions:
        print(f"\n测试情感: {emotion}")
        test_live2d_backend(server_url, emotion)
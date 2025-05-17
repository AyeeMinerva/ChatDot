import requests
import time

def send_chunks(url, text, chunk_size=200, delay=0.02):
    """
    将text分割为chunk_size大小的块，逐块POST到url，适合测试你的HTTP服务器。
    """
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    for idx, chunk in enumerate(chunks):
        print(f"发送第{idx+1}块: {chunk}")
        try:
            resp = requests.post(url, json={"chunk": chunk})
            print(f"响应: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"发送失败: {e}")
        time.sleep(delay)

if __name__ == "__main__":
    # 你的服务器地址
    url = "http://localhost:9000/chunk"
    # 测试字符串
    text = """<live2d>happy</live2d><tts>你好呀！很高兴见到你！</tts><Action><Game Intent></Game Intent></Action>"""
    send_chunks(url, text)
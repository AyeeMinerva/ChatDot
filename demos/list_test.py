# model_list_test.py  (极简模型列表测试脚本)

import os
os.environ['PYTHONIOENCODING'] = 'UTF-8' # 强制 UTF-8 编码 (再次尝试)

from llm_client import LLMClient
import locale

print(f"当前 Python 默认编码: {locale.getpreferredencoding()}") # 打印当前编码

#  !!!  请根据您的实际 API 服务配置修改以下参数  !!!
API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"  #  Ollama API Base URL (请修改为您实际的 API 地址)
MODEL_NAME = "gemini-1.5-flash" #  Ollama 模型名称 (请修改为您要测试的模型)
API_KEY = "?" #  Ollama 通常不需要 API Key,  如果需要，请设置为您的 API Key (请确保是 ASCII 字符)
#  !!!  请确保 API_KEY 和 API_BASE_URL  只包含 ASCII 字符  !!!


# 初始化 LLMClient 实例 (使用 Ollama 配置)
test_client = LLMClient(
    api_base=API_BASE_URL,
    api_key=API_KEY,
    model_name=MODEL_NAME,
    stream=False  #  非流式，简化测试
)

try:
    print("\n开始获取模型列表...")
    models = test_client.fetch_available_models()
    print("\n模型列表获取成功 (UTF-8 编码):")
    for model_name in models:
        print(f"- {model_name}")
    print("\n--- 模型列表获取测试成功 ---") #  明确标记测试成功

except RuntimeError as e:
    print(f"\n!!! 模型列表获取失败 !!!")
    print(f"错误信息 (完整 traceback):\n{e}") # 打印完整错误信息
    print("\n--- 模型列表获取测试失败 ---") # 明确标记测试失败

print("\n--- 测试脚本执行结束 ---") #  脚本结束标记
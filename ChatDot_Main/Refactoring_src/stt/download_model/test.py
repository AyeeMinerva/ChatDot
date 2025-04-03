from funasr import AutoModel

# 模型参数
model_name = "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
model_revision = "v2.0.4"

try:
    print(f"正在尝试下载模型: {model_name}，版本: {model_revision}")
    model_vad = AutoModel(
        model=model_name,
        model_revision=model_revision,
        disable_pbar=False,  # 显示下载进度条
        disable_log=False,   # 显示日志信息
    )
    print("模型下载成功！")
except Exception as e:
    print(f"模型下载失败: {e}")
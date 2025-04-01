"""
# WebAPI文档
` python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml `
## 执行参数:
    `-a` - `绑定地址, 默认"127.0.0.1"`
    `-p` - `绑定端口, 默认9880`
    `-c` - `TTS配置文件路径, 默认"GPT_SoVITS/configs/tts_infer.yaml"`

## API接口调用说明见下方代码

## API接口返回值说明
RESP:
成功: 直接返回 wav 音频流， http code 200
失败: 返回包含错误信息的 json, http code 400


/*-------------------------------------------*/
## 命令控制
endpoint: `/control`

command:
"restart": 重新运行
"exit": 结束运行

GET:
http://127.0.0.1:9880/control?command=restart

POST:
json:
{
    "command": "restart"
}

RESP: 无


/*-------------------------------------------*/
## 切换GPT模型

endpoint: `/set_gpt_weights`

GET:
http://127.0.0.1:9880/set_gpt_weights?weights_path=GPT_SoVITS/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt

RESP: 
成功: 返回"success", http code 200
失败: 返回包含错误信息的 json, http code 400


/*-------------------------------------------*/
## 切换Sovits模型
endpoint: `/set_sovits_weights`

GET:
http://127.0.0.1:9880/set_sovits_weights?weights_path=GPT_SoVITS/pretrained_models/s2G488k.pth

RESP: 
成功: 返回"success", http code 200
失败: 返回包含错误信息的 json, http code 400
"""

import requests
import json

BASE_URL = "http://183.175.12.68:9880"  # API的基础URL，请根据实际情况修改

def tts_inference_get(text, text_lang, ref_audio_path, prompt_lang, prompt_text, text_split_method="cut5", batch_size=1, media_type="wav", streaming_mode=True):
    """使用GET方法进行TTS推理"""
    url = f"{BASE_URL}/tts"
    params = {
        "text": text,  # str, 需要合成语音的文本内容 (必需)
        "text_lang": text_lang,  # str, 文本内容的语言，例如 "zh" 表示中文 (必需)
        "ref_audio_path": ref_audio_path,  # str, 参考音频文件的路径，用于提供语音的风格和音色 (必需)
        "prompt_lang": prompt_lang,  # str, 提示文本的语言，例如 "zh" 表示中文 (必需)
        "prompt_text": prompt_text,  # str, 用于参考音频的提示文本，帮助模型理解参考音频的语音风格 (可选)
        "text_split_method": text_split_method,  # str, 文本分割方法，用于分割长文本，例如 "cut5" (可选，默认 "cut5")
        "batch_size": batch_size,  # int, 推理的批处理大小，一次处理多个文本片段 (可选，默认 1)
        "media_type": media_type,  # str, 返回音频的媒体类型，例如 "wav" (可选，默认 "wav")
        "streaming_mode": streaming_mode  # bool, 是否返回流式响应，如果为 True，则音频数据以流的形式返回 (可选，默认 True)
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.content  # 返回音频数据
    else:
        print(f"API请求失败，状态码：{response.status_code}")
        print(f"响应内容：{response.text}") # 打印响应的内容
        try:
            return response.json()  # 尝试解析JSON
        except json.JSONDecodeError:
            return {"error": "API返回非JSON格式的错误信息", "text": response.text} # 返回错误信息

def tts_inference_post(text, text_lang, ref_audio_path, prompt_lang, prompt_text, aux_ref_audio_paths=[], top_k=5, top_p=1, temperature=1, text_split_method="cut0", batch_size=1, batch_threshold=0.75, split_bucket=True, speed_factor=1.0, streaming_mode=False, seed=-1, parallel_infer=True, repetition_penalty=1.35, sample_steps=32, super_sampling=False):
    """使用POST方法进行TTS推理"""
    url = f"{BASE_URL}/tts"
    payload = {
        "text": text,  # str, 需要合成语音的文本内容 (必需)
        "text_lang": text_lang,  # str, 文本内容的语言 (必需)
        "ref_audio_path": ref_audio_path,  # str, 参考音频文件的路径 (必需)
        "aux_ref_audio_paths": aux_ref_audio_paths,  # list, 用于多说话人音色融合的辅助参考音频文件路径列表 (可选，默认 [])
        "prompt_text": prompt_text,  # str, 参考音频的提示文本 (可选)
        "prompt_lang": prompt_lang,  # str, 提示文本的语言 (必需)
        "top_k": top_k,  # int, top k 采样 (可选，默认 5)
        "top_p": top_p,  # float, top p 采样 (可选，默认 1)
        "temperature": temperature,  # float, 采样的温度 (可选，默认 1)
        "text_split_method": text_split_method,  # str, 文本分割方法 (可选，默认 "cut0")
        "batch_size": batch_size,  # int, 推理的批处理大小 (可选，默认 1)
        "batch_threshold": batch_threshold,  # float, 批处理分割的阈值 (可选，默认 0.75)
        "split_bucket": split_bucket,  # bool, 是否将批处理分割成多个存储桶 (可选，默认 True)
        "speed_factor": speed_factor,  # float, 控制合成音频的速度 (可选，默认 1.0)
        "streaming_mode": streaming_mode,  # bool, 是否返回流式响应 (可选，默认 False)
        "seed": seed,  # int, 用于重现性的随机种子 (可选，默认 -1)
        "parallel_infer": parallel_infer,  # bool, 是否使用并行推理 (可选，默认 True)
        "repetition_penalty": repetition_penalty,  # float, T2S模型的重复惩罚 (可选，默认 1.35)
        "sample_steps": sample_steps,  # int, VITS 模型 V3 的采样步数 (可选，默认 32)
        "super_sampling": super_sampling  # bool, 使用 VITS 模型 V3 时，是否对音频进行超采样 (可选，默认 False)
    }
    print("POST请求 payload:", payload) #打印payload
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.content  # 返回音频数据
    else:
        print(f"POST请求失败，状态码：{response.status_code}")
        print(f"响应内容：{response.text}")
        try:
            return response.json()  # 尝试解析JSON
        except json.JSONDecodeError:
            return {"error": "API返回非JSON格式的错误信息", "text": response.text}

# 示例调用

#GET请求示例
get_audio_data = tts_inference_get(
    text=input("请输入文本："),
    text_lang="zh",
    ref_audio_path="/data/qinxu/GPT-SoVITS/sample_audios/37_也许过大的目标会导致逻辑上的越界.wav",
    prompt_lang="zh",
    prompt_text="也许过大的目标会导致逻辑上的越界"
)

# # GET请求示例
# get_audio_data = tts_inference_get(
#     text="先帝创业未半而中道崩殂，今天下三分，益州疲弊，此诚危急存亡之秋也。",
#     text_lang="zh",
#     ref_audio_path="/data/qinxu/GPT-SoVITS/output/slicer_opt/录音 3.wav_0000005440_0000127680.wav",
#     prompt_lang="zh",
#     prompt_text="也许过大的目标会导致逻辑上的越界"
# )

if isinstance(get_audio_data, bytes):
    with open("output_get.wav", "wb") as f:
        f.write(get_audio_data)
    print("GET请求成功，音频已保存到 output_get.wav")
else:
    print("GET请求失败:", get_audio_data)

# # POST请求示例
# post_audio_data = tts_inference_post(
#     text="你好，世界！",
#     text_lang="zh",
#     ref_audio_path="/data/qinxu/GPT-SoVITS/output/slicer_opt/录音 2.wav_0000036160_0000214080.wav",
#     prompt_lang="zh",
#     prompt_text="一个全新的洞穴，还有这些似曾相识的角度与曲线。"
# )

# if isinstance(post_audio_data, bytes):
#     with open("output_post.wav", "wb") as f:
#         f.write(post_audio_data)
#     print("POST请求成功，音频已保存到 output_post.wav")
# else:
#     print("POST请求失败:", post_audio_data)
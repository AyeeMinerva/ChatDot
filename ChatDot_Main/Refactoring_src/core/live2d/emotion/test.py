from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline
import os

# 定义模型本地保存路径（相对路径）
model_dir = "models/bert-multilingual-go-emtions"
# 绝对路径，用于首次下载
abs_model_path = os.path.join(os.path.dirname(__file__), model_dir)

# 确保模型目录存在
os.makedirs(abs_model_path, exist_ok=True)

# 检查模型是否已经下载到本地
if not os.path.exists(os.path.join(abs_model_path, "model.safetensors")):
    print("正在下载模型到本地，首次下载可能需要几分钟...")
    # 下载模型和分词器到本地
    temp_tokenizer = AutoTokenizer.from_pretrained("SchuylerH/bert-multilingual-go-emtions")
    temp_model = AutoModelForSequenceClassification.from_pretrained("SchuylerH/bert-multilingual-go-emtions")
    
    # 保存到本地
    temp_tokenizer.save_pretrained(abs_model_path)
    temp_model.save_pretrained(abs_model_path)
    print(f"模型已保存到: {abs_model_path}")

# 使用绝对路径加载模型和分词器
tokenizer = AutoTokenizer.from_pretrained(abs_model_path)
model = AutoModelForSequenceClassification.from_pretrained(abs_model_path)

text = "I love you."
nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

result = nlp(text)

print(result)

while True:
    text = input("请输入文本: ")
    result = nlp(text)
    print(result)
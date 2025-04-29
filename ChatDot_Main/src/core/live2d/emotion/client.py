from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline
import os
from threading import Lock, Event
import threading
from global_managers.logger_manager import LoggerManager


class EmotionClient:
    _instance = None
    _lock = Lock()  # 用于线程安全的单例实现

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(EmotionClient, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):  # 防止重复初始化
            self._initialized = True
            self.is_initialized = False  # 初始化状态标志
            self._init_event = Event()  # 用于等待初始化完成
            threading.Thread(target=self._initialize_model, daemon=True).start()  # 异步初始化模型

    def _initialize_model(self):
        """
        异步初始化模型
        """
        try:
            LoggerManager().get_logger().debug("正在初始化情感分析模型...")
            # 定义模型本地保存路径（相对路径）
            model_dir = "models/bert-multilingual-go-emtions"
            # 绝对路径，用于首次下载
            abs_model_path = os.path.join(os.path.dirname(__file__), model_dir)

            # 确保模型目录存在
            os.makedirs(abs_model_path, exist_ok=True)

            # 检查模型是否已经下载到本地
            if not os.path.exists(os.path.join(abs_model_path, "model.safetensors")):
                LoggerManager().get_logger().debug("正在下载模型到本地，首次下载可能需要几分钟...")
                # 下载模型和分词器到本地
                temp_tokenizer = AutoTokenizer.from_pretrained("SchuylerH/bert-multilingual-go-emtions")
                temp_model = AutoModelForSequenceClassification.from_pretrained("SchuylerH/bert-multilingual-go-emtions")
                
                # 保存到本地
                temp_tokenizer.save_pretrained(abs_model_path)
                temp_model.save_pretrained(abs_model_path)
                LoggerManager().get_logger().debug(f"模型已保存到: {abs_model_path}")

            # 使用绝对路径加载模型和分词器
            self.tokenizer = AutoTokenizer.from_pretrained(abs_model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(abs_model_path)
            self.nlp = pipeline("sentiment-analysis", model=self.model, tokenizer=self.tokenizer)

            LoggerManager().get_logger().debug("模型初始化完成")
        except Exception as e:
            LoggerManager().get_logger().warning(f"模型初始化失败: {e}")
        finally:
            self.is_initialized = True
            self._init_event.set()  # 通知等待的线程初始化完成

    def analyze_emotion(self, text: str) -> str:
        """
        接收字符串并返回情感类型字符串
        如果模型未初始化，则等待初始化完成
        """
        if not self.is_initialized:
            LoggerManager().get_logger().debug("模型尚未初始化，等待初始化完成...")
            self._init_event.wait()  # 等待初始化完成

        try:
            result = self.nlp(text)
            if result and len(result) > 0:
                return result[0]['label']  # 返回情感类型
            return "未知情感"
        except Exception as e:
            LoggerManager().get_logger().warning(f"情感分析失败: {e}")
            return "错误"

# 示例用法
if __name__ == "__main__":
    analyzer = EmotionClient()
    while True:
        text = input("请输入文本: ")
        if text.lower() == "exit":
            print("退出程序")
            break
        emotion = analyzer.analyze_emotion(text)
        print(f"情感类型: {emotion}")
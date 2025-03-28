import threading
import queue
from typing import List, Dict, Optional, Iterator

class LLMWorker(threading.Thread):
    """LLM工作线程，使用队列实现实时数据流"""
    
    def __init__(self, llm_client, messages: List[Dict], model_name: str = None, 
                 model_params: Optional[Dict] = None):
        super().__init__()
        self.llm_client = llm_client
        self.messages = messages
        self.model_name = model_name
        self.model_params = model_params or {}
        self._is_running = True
        # 使用队列进行线程间通信
        self.response_queue = queue.Queue()
        self.done = False  # 标记响应是否完成

    def run(self) -> None:
        """执行LLM通信，将响应放入队列"""
        try:
            response = self.llm_client.communicate(
                messages=self.messages,
                model_name=self.model_name,
                model_params_override=self.model_params
            )
            
            # 处理响应
            if isinstance(response, Iterator):
                for chunk in response:
                    if not self._is_running:
                        break
                    if chunk:
                        # 将每个片段放入队列
                        self.response_queue.put(chunk)
            else:
                # 非流式响应，直接放入队列
                self.response_queue.put(response)
                
        except Exception as e:
            # 异常情况，发送错误消息
            self.response_queue.put(f"Error: {str(e)}")
        finally:
            # 标记响应完成
            self.done = True
            # 添加结束标记
            self.response_queue.put(None)

    def stop(self) -> None:
        """停止工作线程"""
        self._is_running = False

    def get_response(self) -> Iterator[str]:
        """
        返回实时响应迭代器
        
        使用生成器实时获取队列中的响应片段
        """
        while True:
            # 从队列中获取一个响应片段
            chunk = self.response_queue.get()
            
            # None 是结束标记
            if chunk is None:
                break
                
            yield chunk
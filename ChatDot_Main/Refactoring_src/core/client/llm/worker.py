import threading
from typing import List, Dict, Optional, Iterator

class LLMWorker(threading.Thread):
    """LLM工作线程，使用迭代器模式处理响应"""
    
    def __init__(self, llm_client, messages: List[Dict], model_name: str = None, 
                 model_params: Optional[Dict] = None):
        super().__init__()
        self.llm_client = llm_client
        self.messages = messages
        self.model_name = model_name
        self.model_params = model_params or {}
        self._is_running = True
        self.response_chunks: List[str] = []

    def run(self) -> None:
        """执行LLM通信，返回响应迭代器"""
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
                        self.response_chunks.append(chunk)
            else:
                self.response_chunks.append(response)
                
        except Exception as e:
            self.response_chunks.append(f"Error: {str(e)}")

    def stop(self) -> None:
        """停止工作线程"""
        self._is_running = False

    def get_response(self) -> List[str]:
        """获取响应片段列表"""
        return self.response_chunks
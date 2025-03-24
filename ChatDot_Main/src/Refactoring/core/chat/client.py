from typing import Callable, List, Dict, Optional, Tuple
from core.chat.context_handle.manager import ContextHandleManager

class ChatClient:
    def __init__(self):
        self.context_manager = ContextHandleManager()
        self.messages: List[Dict] = []

    def send_message(self, message: str, is_stream: bool = False, 
                    on_stream: Optional[Callable[[str], None]] = None,
                    on_error: Optional[Callable[[str], None]] = None) -> Tuple[str, List[Dict], List[Dict]]:
        """
        发送消息并处理上下文
        
        Args:
            message: 用户输入的消息
            is_stream: 是否使用流式输出
            on_stream: 流式输出的回调函数
            on_error: 错误处理的回调函数
            
        Returns:
            tuple: (response, local_messages, llm_messages)
            - response: LLM的响应
            - local_messages: 本地保存的消息
            - llm_messages: 发送给LLM的消息
        """
        message_dict = {"role": "user", "content": message}
        self.messages.append(message_dict)
        
        handler = self.context_manager.get_current_handler()
        local_messages, llm_messages = (handler.process_before_send(self.messages) 
                                      if handler else (self.messages, self.messages))

        # 设置模型参数，确保stream参数正确
        model_params = {"stream": is_stream}
        
        try:
            # 调用LLM服务
            if is_stream:
                self.llm_service.send_message_async(
                    llm_messages,
                    model_params_override=model_params,
                    on_stream=on_stream,
                    on_error=on_error
                )
                return None, local_messages, llm_messages
            else:
                response = self.llm_service.send_message(
                    llm_messages,
                    model_params_override=model_params
                )
                return response, local_messages, llm_messages
        except Exception as e:
            if on_error:
                on_error(str(e))
            raise

    def add_response(self, response: str):
        """添加AI响应到消息列表"""
        self.messages.append({
            "role": "assistant",
            "content": response
        })

    def clear_context(self):
        """清除上下文"""
        self.messages = []

    def delete_message(self, index: int):
        """删除指定索引的消息"""
        if 0 <= index < len(self.messages):
            self.messages.pop(index)

    def edit_message(self, index: int, new_content: str):
        """编辑指定索引的消息内容"""
        if 0 <= index < len(self.messages):
            self.messages[index]["content"] = new_content

    def get_messages(self) -> List[Dict]:
        """获取当前所有消息"""
        return self.messages

    def set_messages(self, messages: List[Dict]):
        """设置消息列表"""
        self.messages = messages
from typing import Callable, Iterator, List, Dict, Optional, Tuple
from chat.context_handle.manager import ContextHandleManager

class ChatClient:
    def __init__(self, llm_service=None, context_handle_service=None):
        """
        初始化聊天客户端
        
        Args:
            llm_service: LLM服务实例
            context_handle_service: 上下文处理服务实例
        """
        self.llm_service = llm_service
        self.context_handle_service = context_handle_service
        self.messages: List[Dict] = []

    def initialize(self):
        """初始化客户端"""
        if self.llm_service:
            self.llm_service.initialize()
        
        # 获取上下文处理器管理器
        if self.context_handle_service:
            self.context_manager = self.context_handle_service.manager
        else:
            self.context_manager = ContextHandleManager()

    def send_message(self, message: str, is_stream: bool = True) -> Tuple[List[Dict], Iterator[str]]:
        """
        处理消息并发送到LLM，实时返回响应
        
        Args:
            message: 用户输入的消息
            is_stream: 是否使用流式输出
            
        Returns:
            Tuple[List[Dict], Iterator[str]]: (本地消息列表, 实时响应迭代器)
        """
        # 添加用户消息到历史
        message_dict = {"role": "user", "content": message}
        self.messages.append(message_dict)
        
        # 使用上下文处理器处理消息
        handler = self.context_manager.get_current_handler()
        local_messages, llm_messages = (handler.process_before_send(self.messages) 
                                      if handler else (self.messages, self.messages))
        
        if not self.llm_service:
            raise RuntimeError("LLM服务未初始化")
            
        # 发送消息并获取响应迭代器
        response_iterator = self.llm_service.send_message(
            messages=llm_messages,
            model_params={"stream": is_stream}
        )

        # 创建实时响应迭代器
        def realtime_response():
            full_response = []
            try:
                for chunk in response_iterator:
                    full_response.append(chunk)  # 收集完整响应
                    yield chunk                  # 实时返回每个片段
            finally:
                # 在迭代完成或发生异常时添加到历史
                if full_response:
                    self.add_response(''.join(full_response))

        return local_messages, realtime_response()

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
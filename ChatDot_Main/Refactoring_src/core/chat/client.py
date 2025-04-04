from typing import Callable, Iterator, List, Dict, Optional, Tuple
#from chat.context_handle.manager import ContextHandleManager
from global_managers.service_manager import ServiceManager
from global_managers.logger_manager import LoggerManager
from chat.persistence import ChatPersistence

class ChatClient:
    def __init__(self, llm_service=None, service_manager=None, chat_persistence=None):
        """
        初始化聊天客户端
        
        Args:
            llm_service: LLM服务实例
            context_handle_service: 上下文处理服务实例
        """
        self.llm_service = llm_service
        self.service_manager = service_manager or ServiceManager()
        self.context_handle_service = self.service_manager.get_service("context_handle_service")
        self.live2d_service = self.service_manager.get_service("live2d_service")
        self.tts_service = self.service_manager.get_service("tts_service")
        self.chat_persistence = chat_persistence or ChatPersistence()
        self._is_Stop_generating = False  # 停止生成标志
        self.messages: List[Dict] = []

    def initialize(self):
        """初始化客户端"""
        if self.llm_service:
            self.llm_service.initialize()
            
    def stop_generating(self):
        """停止生成"""
        self._is_Stop_generating = True
        try:
            self.llm_service.stop_generating()
        except Exception as e:
            LoggerManager().get_logger().warning(f"chat.client: llm_service级停止生成失败: {e}")

    def send_message(self, message: str, is_stream: bool = True) -> Tuple[List[Dict], Iterator[str]]:
        """
        处理消息并发送到LLM，实时返回响应
        
        Args:
            message: 用户输入的消息
            is_stream: 是否使用流式输出
            
        Returns:
            Tuple[List[Dict], Iterator[str]]: (本地消息列表, 实时响应迭代器)
        """
        ### 初始化标志
        self._is_Stop_generating = False  # 重置停止生成标志
        #region 消息前处理
        ################################
        # 消息前处理
        #
        # 添加用户消息到历史
        self.add_response("user", message)
        
        # 使用上下文处理器处理消息
        handler = self.context_handle_service.get_current_handler()
        local_messages, llm_messages = (handler.process_before_send(self.messages) 
                                      if handler else (self.messages, self.messages))
        
        if not self.llm_service:
            raise RuntimeError("LLM服务未初始化")
        #endregion 消息前处理
        
        #region 发送消息
        ##############################
        # 发送消息
        #
        # 发送消息并获取响应迭代器
        response_iterator = self.llm_service.send_message(
            messages=llm_messages,
            model_params={"stream": is_stream}
        )
        #endregion 发送消息

        #region 接收消息及后处理(阻塞)
        ##############################
        # 接收消息及后处理
        #
        # 创建实时响应迭代器
        ttsenabled = self.tts_service and self.tts_service.is_tts_enabled()
        if ttsenabled:
            LoggerManager().get_logger().info("TTS服务已启用...")
            
        def realtime_response():
            full_response = []
            try:
                for chunk in response_iterator:
                    full_response.append(chunk)  # 收集完整响应
                    # 检查是否需要停止生成
                    if self._is_Stop_generating:#实时打断
                        break
                    
                    #tts
                    if ttsenabled:
                        LoggerManager().get_logger().debug(f"实时播放文本到语音: {chunk}")
                        self.tts_service.realtime_play_text_to_speech(chunk)
                        
                    yield chunk# 实时返回每个片段
            finally:
                # 在迭代完成或发生异常时添加到历史
                if full_response:
                    #添加到历史前经过处理器处理
                    if handler:
                        processed_response = handler.process_before_show(''.join(full_response))
                    else:
                        processed_response = ''.join(full_response)
                    self.add_response("assistant", processed_response)
                    #self.add_response(''.join(full_response))
                    
                    #调用live2d服务
                    # 如果 Live2D 启用，则调用 Live2D 服务
                    if self.live2d_service and self.live2d_service.is_live2d_enabled():
                        LoggerManager().get_logger().debug("调用 Live2D 服务...")
                        self.live2d_service.text_to_live2d(processed_response)
                    #调用tts服务
                    if ttsenabled:
                        self.tts_service.realtime_play_text_to_speech(force_process=True)  # 处理剩余缓冲区
                        LoggerManager().get_logger().debug("TTS流处理完成...")
                    #if self.tts_service and self.tts_service.is_tts_enabled():
                        #LoggerManager().get_logger().debug("调用 TTS 服务...")
                        #self.tts_service.text_to_speech(processed_response)#调用此不会播放音频
                        # 直接播放音频
                        #self.tts_service.play_text_to_speech(processed_response)
                
                        
        #endregion 接收消息及后处理(阻塞)
                    
        #region 消息后处理(非阻塞)
        #此部分不应直接使用，应当将非阻塞操作放置到对应的service中,时间较长的操作应该自行实现异步处理
        #endregion 消息后处理(非阻塞)

        return local_messages, realtime_response()

    def add_response(self, role: str, response: str):
        """添加消息到消息列表"""
        self.messages.append({"role": role, "content": response})
        self.chat_persistence.save_history(self.messages)
        
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
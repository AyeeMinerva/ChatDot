from typing import Tuple, Dict, Any

class BaseTTSHandler:
    """TTS处理器的基础类，所有处理器必须继承此类"""
    
    def process_text_chunk(self, text_chunk: str, buffer: str, force_process: bool = False) -> Tuple[str, str]:
        """
        处理文本块
        
        Args:
            text_chunk: 当前接收的文本块
            buffer: 当前缓冲区内容
            force_process: 是否强制处理所有内容
            
        Returns:
            tuple[str, str]: (要处理的文本, 更新后的缓冲区)
        """
        raise NotImplementedError("必须实现process_text_chunk方法")
    
    def get_handler_info(self) -> Dict[str, Any]:
        """获取处理器信息"""
        return {
            "name": "基础TTS处理器",
            "description": "抽象基类，不应直接使用"
        }
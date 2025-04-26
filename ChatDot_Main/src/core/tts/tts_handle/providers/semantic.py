from tts.tts_handle.base import BaseTTSHandler
from typing import Tuple, Dict, Any

class ContextHandler(BaseTTSHandler):
    """基于语义单元的TTS处理器"""
    
    def process_text_chunk(self, text_chunk: str, buffer: str, force_process: bool = False) -> Tuple[str, str]:
        """按语义单元（逗号、分号等）处理文本"""
        new_buffer = buffer + (text_chunk or "")
        
        if not new_buffer:
            return "", new_buffer
            
        if force_process:
            return new_buffer.strip(), ""
            
        # 语义单元分隔符
        semantic_separators = ["，", "；", ",", ";", "：", ":", "、"]
        
        # 寻找语义单元分隔符
        process_index = -1
        for sep in semantic_separators:
            pos = new_buffer.rfind(sep)
            if pos > process_index:
                process_index = pos
                
        # 处理找到的语义单元
        if process_index >= 0:
            process_text = new_buffer[:process_index + 1]
            remaining_buffer = new_buffer[process_index + 1:]
            return process_text, remaining_buffer
            
        return "", new_buffer
        
    def get_handler_info(self) -> Dict[str, Any]:
        return {
            "name": "语义单元处理器",
            "description": "按语义单元处理文本，在逗号、分号等处分割，平衡流畅度和实时性"
        }
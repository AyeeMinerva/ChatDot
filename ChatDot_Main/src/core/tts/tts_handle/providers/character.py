from tts.tts_handle.base import BaseTTSHandler
from typing import Tuple, Dict, Any

class ContextHandler(BaseTTSHandler):
    """基于字符数的TTS处理器"""
    
    def __init__(self, char_threshold=30):
        self.char_threshold = char_threshold
    
    def process_text_chunk(self, text_chunk: str, buffer: str, force_process: bool = False) -> Tuple[str, str]:
        """累积到一定字符数后处理"""
        new_buffer = buffer + (text_chunk or "")
        
        if not new_buffer:
            return "", new_buffer
            
        if force_process:
            return new_buffer.strip(), ""
            
        # 达到字符阈值时处理
        if len(new_buffer) >= self.char_threshold:
            return new_buffer, ""
            
        return "", new_buffer
        
    def get_handler_info(self) -> Dict[str, Any]:
        return {
            "name": "字符累积处理器",
            "description": f"累积{self.char_threshold}个字符后处理，适合快速响应"
        }
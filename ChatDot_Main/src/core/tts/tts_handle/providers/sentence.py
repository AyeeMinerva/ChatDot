from tts.tts_handle.base import BaseTTSHandler
from typing import Tuple, Dict, Any

class ContextHandler(BaseTTSHandler):
    """基于句子的TTS处理器，根据句子结束标点分割文本"""
    
    def process_text_chunk(self, text_chunk: str, buffer: str, force_process: bool = False) -> Tuple[str, str]:
        """按句子切分文本"""
        new_buffer = buffer + (text_chunk or "")
        
        if not new_buffer:
            return "", new_buffer
            
        if force_process:
            return new_buffer.strip(), ""
            
        # 句子结束标点
        sentence_end_punctuation = ["。", "！", "？", ".", "!", "?", "\n"]
        
        # 寻找句子结束标点
        process_index = -1
        for punct in sentence_end_punctuation:
            pos = new_buffer.rfind(punct)
            if pos > process_index:
                process_index = pos
                
        # 处理找到的句子
        if process_index >= 0:
            process_text = new_buffer[:process_index + 1]
            remaining_buffer = new_buffer[process_index + 1:]
            return process_text, remaining_buffer
            
        return "", new_buffer
        
    def get_handler_info(self) -> Dict[str, Any]:
        return {
            "name": "句子级处理器",
            "description": "按完整句子处理文本，在句子结束标点处分割，适合流畅朗读"
        }
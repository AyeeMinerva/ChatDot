from tts.tts_handle.base import BaseTTSHandler
from typing import Tuple, Dict, Any

class ContextHandler(BaseTTSHandler):
    """
    基于<tts>标签和句子分割的TTS处理器。
    仅处理<tts>...</tts>标签内的文本，并按句子结束标点分割。
    能够处理跨多个文本块（chunk）的标签和句子。
    """
    def __init__(self):
        """初始化处理器状态。"""
        self._buffer = ""  # 用于累积跨块的文本
        self._in_tts_tag = False  # 标记当前是否在<tts>标签内
        # 定义句子结束标点
        self._sentence_end_punctuation = ["。", "！", "？", ".", "!", "?", "\n"]
        self._start_tag = "<tts>"
        self._end_tag = "</tts>"

    def _find_last_sentence_end(self, text: str) -> int:
        """在文本中查找最后一个句子结束标点的位置。""" 
        last_pos = -1
        for punct in self._sentence_end_punctuation:
            # 使用rfind从右侧查找最后一个标点
            pos = text.rfind(punct)
            if pos > last_pos:
                last_pos = pos
        return last_pos

    def process_text_chunk(self, text_chunk: str, buffer: str, force_process: bool = False) -> Tuple[str, str]:
        """
        处理传入的文本块，结合之前的缓冲区内容，提取<tts>标签内的完整句子。

        Args:
            text_chunk: 新传入的文本块，可能为None或空字符串。
            buffer: 上一次调用遗留的缓冲内容。
            force_process: 是否强制处理缓冲区中剩余的所有有效内容（标签内未结束的句子或整个缓冲区）。

        Returns:
            一个元组 (processed_text, new_buffer):
            - processed_text: 本次调用提取到的、属于<tts>标签内的完整句子组合。
            - new_buffer: 更新后的缓冲区内容，供下一次调用使用。
        """
        # 合并旧缓冲区和新文本块
        self._buffer = buffer + (text_chunk or "")
        processed_text = "" # 本次调用要返回的文本

        while True: # 循环处理，直到缓冲区没有更多可处理的内容或状态不再改变
            if not self._buffer: # 如果缓冲区为空，则退出
                break

            initial_buffer_state = self._buffer
            initial_tag_state = self._in_tts_tag

            if not self._in_tts_tag:
                # 当前不在<tts>标签内，查找起始标签
                start_tag_index = self._buffer.find(self._start_tag)
                if start_tag_index != -1:
                    # 找到起始标签，丢弃标签前的内容，更新缓冲区和状态
                    self._buffer = self._buffer[start_tag_index + len(self._start_tag):]
                    self._in_tts_tag = True
                else:
                    # 未找到起始标签
                    if force_process:
                        # 强制处理时，丢弃所有不在标签内的内容
                        self._buffer = ""
                    # 否则，保留缓冲区内容等待更多输入，退出循环
                    break

            elif self._in_tts_tag:
                # 当前在<tts>标签内，查找结束标签
                end_tag_index = self._buffer.find(self._end_tag)
                if end_tag_index != -1:
                    # 找到结束标签
                    content_in_tag = self._buffer[:end_tag_index]
                    remaining_after_tag = self._buffer[end_tag_index + len(self._end_tag):]

                    # 在标签内容中查找最后一个句子结束标点
                    last_punct_index = self._find_last_sentence_end(content_in_tag)

                    if last_punct_index != -1:
                        # 找到完整句子
                        sentences_to_add = content_in_tag[:last_punct_index + 1].strip()
                        remaining_in_tag = content_in_tag[last_punct_index + 1:] # 句子结束后的剩余部分
                        if sentences_to_add:
                            # 累加处理好的句子，如果已有内容则加空格分隔
                            processed_text += (" " if processed_text else "") + sentences_to_add
                        # 更新缓冲区：标签内剩余部分 + 标签外剩余部分
                        self._buffer = remaining_in_tag + remaining_after_tag
                    else:
                        # 标签内没有找到完整句子结束标点，丢弃这部分内容
                        # （因为遇到了结束标签，这部分无法构成完整句子）
                        self._buffer = remaining_after_tag

                    # 状态变为不在标签内
                    self._in_tts_tag = False
                else:
                    # 未找到结束标签，当前缓冲区全部内容都在<tts>标签内（或其开始部分）
                    last_punct_index = self._find_last_sentence_end(self._buffer)
                    if last_punct_index != -1:
                        # 在当前缓冲区（标签内）找到完整句子
                        sentences_to_add = self._buffer[:last_punct_index + 1].strip()
                        if sentences_to_add:
                            processed_text += (" " if processed_text else "") + sentences_to_add
                        # 更新缓冲区为剩余部分
                        self._buffer = self._buffer[last_punct_index + 1:]
                        # 已处理部分句子，但仍在标签内，退出当前处理循环，等待更多数据或结束标签
                        # 返回已处理的句子和剩余的缓冲区
                        break
                    else:
                        # 缓冲区内（标签内）未找到完整句子
                        if force_process:
                            # 强制处理，将当前缓冲区（标签内）所有内容视为要处理的文本
                            sentences_to_add = self._buffer.strip()
                            if sentences_to_add:
                                processed_text += (" " if processed_text else "") + sentences_to_add
                            # 清空缓冲区，因为已被强制处理
                            self._buffer = ""
                            # 状态保持在标签内，但缓冲区已空
                        else:
                            # 不强制处理，保留缓冲区，等待更多数据或结束标签，退出循环
                            break

            # 防止无限循环：如果缓冲区和标签状态在一轮处理后没有变化，则退出
            if self._buffer == initial_buffer_state and self._in_tts_tag == initial_tag_state:
                break

        # 返回本次处理累积的文本和最终的缓冲区状态
        return processed_text, self._buffer

    def get_handler_info(self) -> Dict[str, Any]:
        """返回处理器的信息。"""
        return {
            "name": "TTS标签句子处理器",
            "description": "仅处理<tts>标签内的文本，并按完整句子分割（句末标点）"
        }

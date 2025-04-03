"""
STT服务测试脚本
"""
from .stt_service import STTService
import time

def segment_callback(text: str) -> None:
    """只接收完整结果"""
    print(f"\n收到完整语音识别结果: {text}")

def main():
    # 创建STT服务
    stt = STTService()
    
    # 添加回调
    stt.add_segment_callback(segment_callback)
    
    # 初始化服务
    print("初始化STT服务，这可能需要一点时间来加载模型...")
    if not stt.initialize():
        print("初始化STT服务失败")
        return
    
    print("开始语音识别，只显示完整结果...")
    print("按Ctrl+C停止")
    
    # 启动识别
    if not stt.start_recognition():
        print("启动语音识别失败")
        stt.shutdown()
        return
    
    try:
        # 持续运行直到用户中断
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        # 停止识别并关闭服务
        stt.stop_recognition()
        stt.shutdown()
        print("\n已关闭STT服务")

if __name__ == "__main__":
    main()
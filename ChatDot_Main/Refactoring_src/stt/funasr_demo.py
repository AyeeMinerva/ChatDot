from funasr_manager import RealtimeASR
import asyncio

def segment_callback(text: str) -> None:
    """只接收 2pass-offline 模式的完整结果"""
    print(f"\n收到 2pass-offline 最终结果: {text}")

async def main():
    asr = RealtimeASR(
        host="localhost",
        port=10095,
        use_ssl=False
    )
    
    asr.add_segment_callback(segment_callback)
    print("开始语音识别，只显示 2pass-offline 模式的最终结果...")
    await asr.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n停止语音识别...")
    except Exception as e:
        print(f"发生错误: {e}")
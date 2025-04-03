"""
STT服务测试脚本
"""
import asyncio
import time
from typing import List, Dict, Any
from .service import STTService

def segment_callback(text: str) -> None:
    """识别到完整语音片段的回调"""
    print(f"\n收到语音识别结果: {text}")

async def test_async():
    """异步测试STT服务"""
    print("=== STT服务测试 ===")
    
    # 创建STT服务
    stt = STTService()
    
    # 添加回调
    stt.add_segment_callback(segment_callback)
    
    # 打印当前设置
    print(f"\n当前服务器设置:")
    print(f"- 服务器地址: {stt.settings.get_setting('host')}")
    print(f"- 服务器端口: {stt.settings.get_setting('port')}")
    print(f"- 使用本地服务: {stt.settings.get_setting('use_local_server')}")
    print(f"- 自动启动服务器: {stt.settings.get_setting('auto_start_server')}")
    
    # 修改服务器地址
    server_choice = input("\n选择服务器类型:\n1. 本地服务器 (localhost)\n2. 远程服务器 (183.175.12.68)\n请输入选择 (默认1): ")
    
    if server_choice == "2":
        print("\n切换到远程服务器...")
        stt.update_server_config(
            host="183.175.12.68", 
            port=10095,
            use_local_server=False
        )
    else:
        print("\n使用本地服务器...")
        stt.update_server_config(
            host="localhost", 
            port=10095,
            use_local_server=True
        )
    
    # 初始化服务
    print("\n初始化STT服务，这可能需要一点时间...")
    if not await stt.initialize_async():
        print("初始化STT服务失败")
        return
    
    print("\n开始语音识别，请说话...")
    print("按Ctrl+C停止")
    
    # 启动识别
    if not await stt.start_recognition_async():
        print("启动语音识别失败")
        await stt.shutdown_async()
        return
    
    try:
        # 持续运行直到用户中断
        while True:
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        # 停止识别并关闭服务
        print("\n关闭服务...")
        await stt.stop_recognition_async()
        await stt.shutdown_async()
        print("测试完成")

def main():
    """主函数"""
    try:
        asyncio.run(test_async())
    except KeyboardInterrupt:
        print("\n测试被中断")
    except Exception as e:
        print(f"\n测试过程中出错: {e}")

if __name__ == "__main__":
    main()
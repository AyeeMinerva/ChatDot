import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import time
from global_managers.ProcessCommunicator import ProcessCommunicator

if __name__ == "__main__":
    # 获取客户端模式的单例
    comm = ProcessCommunicator.instance(is_server=False)
    comm.active = True

    # 示例发送Game.Description
    desc = "你现在在一个神秘的森林中，四周充满未知。"
    comm.send(desc, "Game.Description")
    print(f"已发送 Game.Description: {desc}")

    # 示例发送Game.Choice
    choice = "向北走"
    comm.send(choice, "Game.Choice")
    print(f"已发送 Game.Choice: {choice}")

    # 保持进程一会儿，便于观察
    print("等待5秒后退出...")
    time.sleep(5)

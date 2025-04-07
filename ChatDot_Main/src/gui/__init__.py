import os
import sys

# 获取 gui 目录的路径
gui_dir = os.path.dirname(os.path.abspath(__file__))

# 将 gui 目录添加到 Python 搜索路径
if gui_dir not in sys.path:
    sys.path.insert(0, gui_dir)

# 将 parent 目录添加到搜索路径
parent_dir = os.path.dirname(gui_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
import os
import sys

# 获取当前模块(core)的目录路径
core_dir = os.path.dirname(os.path.abspath(__file__))

# 将core目录添加到Python搜索路径中
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)
    
# 将parent目录(Refactoring_src)添加到搜索路径
parent_dir = os.path.dirname(core_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    
#print(f"Python path adjusted in core/__init__.py: {core_dir} added to sys.path")
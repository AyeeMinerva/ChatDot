import os

def get_project_root():
    """
    获取项目根目录的绝对路径，通过固定向上两级目录实现。
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    grandparent_dir = os.path.dirname(parent_dir)
    return grandparent_dir
import os

def get_core_path():
    """
    获取core目录的路径
    通过固定向上跳转一级获取core所在路径
    """
    current_file = os.path.abspath(__file__)
    utils_dir = os.path.dirname(current_file)  # 当前文件所在目录 (utils)
    core_dir = os.path.dirname(utils_dir)      # 向上跳转一级到core目录
    return core_dir
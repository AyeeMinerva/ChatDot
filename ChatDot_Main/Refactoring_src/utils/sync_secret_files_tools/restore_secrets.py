# 暂存/sync/restore_secrets.py
import os
import shutil
import argparse

def restore_secrets(source_dir, destination_dir):
    """
    将文件/文件夹从源目录迁移回目标目录，保留相对目录结构。
    """
    for root, dirs, files in os.walk(source_dir):
        relative_path = os.path.relpath(root, source_dir)
        dest_root = os.path.join(destination_dir, relative_path)

        # 处理文件夹
        for name in dirs:
            source_item_path = os.path.join(root, name)
            dest_item_path = os.path.join(dest_root, name)
            os.makedirs(dest_root, exist_ok=True)
            try:
                shutil.copytree(source_item_path, dest_item_path, dirs_exist_ok=True)
                print(f"已恢复文件夹: {source_item_path} -> {dest_item_path}")
            except Exception as e:
                print(f"恢复文件夹时发生错误: {source_item_path} -> {dest_item_path}, 错误: {e}")

        # 处理文件
        for name in files:
            source_item_path = os.path.join(root, name)
            dest_item_path = os.path.join(dest_root, name)
            os.makedirs(dest_root, exist_ok=True)
            try:
                shutil.copy2(source_item_path, dest_item_path)
                print(f"已恢复文件: {source_item_path} -> {dest_item_path}")
            except Exception as e:
                print(f"恢复文件时发生错误: {source_item_path} -> {dest_item_path}, 错误: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将文件/文件夹从源目录恢复到目标目录。")
    parser.add_argument("source_dir", help="源目录的路径（例如：secrets_backup）")
    parser.add_argument("destination_dir", help="目标目录的路径（例如：项目）")
    args = parser.parse_args()

    source_directory = args.source_dir
    destination_directory = args.destination_dir

    if not os.path.isdir(source_directory):
        print(f"错误: 源目录 '{source_directory}' 不存在或不是一个有效的目录。")
        exit(1)

    if not os.path.isdir(destination_directory):
        print(f"错误: 目标目录 '{destination_directory}' 不存在或不是一个有效的目录。")
        exit(1)

    restore_secrets(source_directory, destination_directory)
    print("文件/文件夹恢复完成。")
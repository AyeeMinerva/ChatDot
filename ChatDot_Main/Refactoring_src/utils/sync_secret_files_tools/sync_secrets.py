# 项目/sync/sync_secrets.py
import os
import shutil
import argparse

def sync_secrets(source_dir, destination_dir):
    """
    将以 "SECRET_" 开头的文件/文件夹，SECRET 文件夹，SECRETS 文件夹，.secret 文件
    从源目录迁移到目标目录，保留相对目录结构。
    """
    items_to_move = ["SECRET", "SECRETS", ".secret"]

    for root, dirs, files in os.walk(source_dir):
        relative_path = os.path.relpath(root, source_dir)
        dest_root = os.path.join(destination_dir, relative_path)

        # 处理文件夹
        for name in dirs:
            if name.startswith("SECRET_") or name in items_to_move:
                source_item_path = os.path.join(root, name)
                dest_item_path = os.path.join(dest_root, name)
                os.makedirs(dest_root, exist_ok=True)
                try:
                    shutil.copytree(source_item_path, dest_item_path)
                    print(f"已复制文件夹: {source_item_path} -> {dest_item_path}")
                except FileExistsError:
                    print(f"警告: 目标文件夹已存在，跳过: {dest_item_path}")
                except Exception as e:
                    print(f"复制文件夹时发生错误: {source_item_path} -> {dest_item_path}, 错误: {e}")

        # 处理文件
        for name in files:
            if name.startswith("SECRET_") or name in items_to_move:
                source_item_path = os.path.join(root, name)
                dest_item_path = os.path.join(dest_root, name)
                os.makedirs(dest_root, exist_ok=True)
                try:
                    shutil.copy2(source_item_path, dest_item_path)  # copy2 保留更多元数据
                    print(f"已复制文件: {source_item_path} -> {dest_item_path}")
                except FileExistsError:
                    print(f"警告: 目标文件已存在，跳过: {dest_item_path}")
                except Exception as e:
                    print(f"复制文件时发生错误: {source_item_path} -> {dest_item_path}, 错误: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将敏感文件/文件夹从源目录迁移到目标目录。")
    parser.add_argument("source_dir", help="源目录的路径（例如：项目）")
    parser.add_argument("destination_dir", help="目标目录的路径")
    args = parser.parse_args()

    source_directory = args.source_dir
    destination_directory = args.destination_dir

    if not os.path.isdir(source_directory):
        print(f"错误: 源目录 '{source_directory}' 不存在或不是一个有效的目录。")
        exit(1)

    os.makedirs(destination_directory, exist_ok=True)
    sync_secrets(source_directory, destination_directory)
    print("敏感文件/文件夹迁移完成。")
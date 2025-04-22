import argparse
import os
import sys
from typing import List, Dict, Any

# 添加项目根目录到 Python 路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))  # 回到ChatDot根目录
sys.path.append(project_root)

from src.core.rag.embedding_service import get_embedding_service
from src.core.rag.vector_store import VectorStore
from src.core.global_managers.logger_manager import LoggerManager

logger = LoggerManager().get_logger()

def read_text_file(file_path: str) -> str:
    """读取文本文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            with open(file_path, 'r', encoding='gbk') as file:
                return file.read()
        except Exception as e:
            logger.error(f"使用 GBK 编码读取文件失败: {e}")
            return ""
    except Exception as e:
        logger.error(f"读取文件 {file_path} 失败: {e}", exc_info=True)
        return ""

def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """将文本分割成重叠的块"""
    if not text:
        return []
    
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if chunk:
            chunks.append(chunk)
    return chunks

def import_document(file_path: str, collection_name: str = "document_store", chunk_size: int = 1000, overlap: int = 200) -> bool:
    """导入文档并存储到向量数据库"""
    # 1. 读取文件
    text = read_text_file(file_path)
    if not text:
        logger.error(f"无法读取文件内容: {file_path}")
        return False
    
    # 2. 分割文本
    chunks = split_text_into_chunks(text, chunk_size, overlap)
    logger.info(f"文件 {file_path} 已分割为 {len(chunks)} 个块")
    
    # 3. 初始化嵌入服务和向量存储
    try:
        embedding_service = get_embedding_service()
        vector_store = VectorStore(collection_name=collection_name)
    except Exception as e:
        logger.error(f"初始化服务失败: {e}", exc_info=True)
        return False
    
    # 4. 嵌入并存储每个块
    successful_chunks = 0
    file_name = os.path.basename(file_path)
    
    for i, chunk in enumerate(chunks):
        try:
            # 生成嵌入
            embedding = embedding_service.embed_text(chunk)
            if not embedding:
                logger.warning(f"块 {i+1}/{len(chunks)} 嵌入失败")
                continue
                
            # 使用特殊格式的 ID
            doc_id = f"doc_{file_name.replace('.', '_')}_{i}"
            
            # 添加到向量存储
            vector_store.add_qa_pair(
                question=f"Document: {file_name}, Chunk {i+1}/{len(chunks)}", 
                answer=chunk,
                embedding=embedding,
                qa_id=doc_id
            )
            
            successful_chunks += 1
            if i % 10 == 0 or i == len(chunks) - 1:
                logger.info(f"进度: {i+1}/{len(chunks)} 块已处理")
                
        except Exception as e:
            logger.error(f"处理块 {i+1}/{len(chunks)} 时出错: {e}", exc_info=True)
    
    logger.info(f"文件导入完成，成功导入 {successful_chunks}/{len(chunks)} 个块")
    return successful_chunks > 0

def main():
    parser = argparse.ArgumentParser(description="将文档导入到向量数据库")
    parser.add_argument("path", help="文件或目录路径")
    parser.add_argument("--collection", default="document_store", help="存储文档的集合名称")
    parser.add_argument("--chunk-size", type=int, default=1000, help="块大小（字符数）")
    parser.add_argument("--overlap", type=int, default=200, help="块重叠（字符数）")
    args = parser.parse_args()
    
    path = args.path
    collection_name = args.collection
    
    logger.info(f"开始导入到集合 '{collection_name}'")
    
    if os.path.isfile(path):
        # 导入单个文件
        success = import_document(path, collection_name, args.chunk_size, args.overlap)
        if success:
            logger.info(f"文件 {path} 导入成功")
            print(f"文件 {path} 导入成功")
        else:
            logger.error(f"文件 {path} 导入失败")
            print(f"文件 {path} 导入失败")
    elif os.path.isdir(path):
        # 导入目录下所有文本文件
        text_extensions = ['.txt', '.md', '.py', '.js', '.html', '.csv', '.json', '.log']
        files_processed = 0
        files_succeeded = 0
        
        for root, _, files in os.walk(path):
            for file in files:
                if any(file.endswith(ext) for ext in text_extensions):
                    file_path = os.path.join(root, file)
                    print(f"正在处理文件: {file_path}")
                    logger.info(f"正在处理文件: {file_path}")
                    files_processed += 1
                    if import_document(file_path, collection_name, args.chunk_size, args.overlap):
                        files_succeeded += 1
        
        logger.info(f"目录导入完成。成功: {files_succeeded}/{files_processed} 文件")
        print(f"目录导入完成。成功: {files_succeeded}/{files_processed} 文件")
    else:
        logger.error(f"路径不存在: {path}")
        print(f"错误: 路径不存在: {path}")

if __name__ == "__main__":
    # 设置控制台编码，以支持中文输出
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass
    
    print(f"文档导入工具 - 将导入到集合中...")
    try:
        main()
        print("导入过程完成")
    except KeyboardInterrupt:
        print("\n用户中断，导入过程已停止")
    except Exception as e:
        logger.error(f"导入过程出错: {e}", exc_info=True)
        print(f"错误: {e}")
        
    # 如果在命令行运行，等待用户按键退出
    if len(sys.argv) > 1:
        input("按回车键退出...")
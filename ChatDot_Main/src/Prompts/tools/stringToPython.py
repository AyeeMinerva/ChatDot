import pyperclip

def convert_to_python_string():
    print("请粘贴要转换的文本 (按Ctrl+D [Unix/Mac] 或 Ctrl+Z [Windows] 然后回车结束输入):")
    
    try:
        # 读取所有输入行
        lines = []
        while True:
            try:
                line = input()
                lines.append(line)
            except EOFError:
                break
    
        # 将所有行合并为一个字符串，处理转义字符
        result = '\n'.join(lines)
        result = result.replace('\\', '\\\\')  # 处理反斜杠
        result = result.replace('"', '\\"')    # 处理双引号
        
        # Add option to print as single line
        single_line_result = result.replace('\n', '\\n')
        print("\n单行格式:")
        print(f'"{single_line_result}"')
        
        pyperclip.copy(f'"{single_line_result}"')
        print("已复制到剪贴板")
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    convert_to_python_string()
from typing import Dict, Callable
from bootstrap import Bootstrap
from global_managers.service_manager import ServiceManager

class ConsoleInterface:
    """控制台交互界面"""
    
    def __init__(self):
        self.bootstrap = Bootstrap()
        self.service_manager = ServiceManager()
        self.commands: Dict[str, Callable] = {
            'help': self.show_help,
            'chat': self.chat_mode,
            'handlers': self.list_handlers,
            'switch': self.switch_handler,
            'clear': self.clear_chat,
            'export': self.export_history,
            'import': self.import_history,
            'models': self.list_models,
            'config': self.configure_llm,
            'exit': lambda: print("退出程序...")
        }

    def run(self):
        """运行控制台界面"""
        print("正在初始化服务...")
        self.bootstrap.initialize()
        print("初始化完成！输入 'help' 查看命令列表")

        while True:
            try:
                command = input("\n> ").strip().lower()
                if command == 'exit':
                    break
                
                if command in self.commands:
                    self.commands[command]()
                else:
                    print("未知命令。输入 'help' 查看可用命令")
                    
            except Exception as e:
                print(f"错误: {str(e)}")

        self.bootstrap.shutdown()

    def show_help(self):
        """显示帮助信息"""
        print("\n可用命令:")
        print("help    - 显示此帮助信息")
        print("chat    - 进入聊天模式")
        print("handlers- 显示可用的上下文处理器")
        print("switch  - 切换上下文处理器")
        print("clear   - 清空聊天历史")
        print("export  - 导出聊天历史")
        print("import  - 导入聊天历史")
        print("models  - 显示可用的LLM模型")
        print("config  - 配置LLM服务")
        print("exit    - 退出程序")

    def chat_mode(self):
        """进入聊天模式"""
        chat_service = self.service_manager.get_service("chat_service")
        print("\n进入聊天模式 (输入 'q' 返回主菜单)")
        
        while True:
            user_input = input("\n用户: ")
            if user_input.lower() == 'q':
                break
                
            print("助手: ", end='', flush=True)
            
            # 使用迭代器处理响应
            try:
                for chunk in chat_service.send_message(user_input, is_stream=True):
                    print(chunk, end='', flush=True)
                print()  # 打印换行
            except Exception as e:
                print(f"\n错误: {str(e)}")

    def list_handlers(self):
        """列出所有可用的上下文处理器"""
        context_service = self.service_manager.get_service("context_handle_service")
        handlers = context_service.get_available_handlers()
        
        print("\n可用的上下文处理器:")
        for handler in handlers:
            print(f"- {handler['name']} ({handler['id']})")
            print(f"  描述: {handler['description']}")
            print(f"  版本: {handler['version']}\n")

    def switch_handler(self):
        """切换上下文处理器"""
        context_service = self.service_manager.get_service("context_handle_service")
        handlers = context_service.get_available_handlers()
        
        print("\n可用的处理器:")
        for handler in handlers:
            print(f"- {handler['id']}: {handler['name']}")
            
        handler_id = input("请输入要切换的处理器ID: ")
        if context_service.set_current_handler(handler_id):
            print(f"成功切换到处理器: {handler_id}")
        else:
            print("切换处理器失败")

    def clear_chat(self):
        """清空聊天历史"""
        chat_service = self.service_manager.get_service("chat_service")
        chat_service.clear_context()
        print("聊天历史已清空")

    def export_history(self):
        """导出聊天历史"""
        chat_service = self.service_manager.get_service("chat_service")
        filepath = input("请输入导出文件路径 (默认为 chat_history.json): ").strip()
        filepath = filepath or "chat_history.json"
        chat_service.export_history(filepath)
        print(f"聊天历史已导出到: {filepath}")

    def import_history(self):
        """导入聊天历史"""
        chat_service = self.service_manager.get_service("chat_service")
        filepath = input("请输入要导入的文件路径: ").strip()
        chat_service.import_history(filepath)
        print("聊天历史导入成功")

    def list_models(self):
        """列出可用的LLM模型"""
        llm_service = self.service_manager.get_service("llm_service")
        models = llm_service.fetch_models()
        print("\n可用的模型:")
        for model in models:
            print(f"- {model}")

    def configure_llm(self):
        """配置LLM服务"""
        llm_service = self.service_manager.get_service("llm_service")
        
        print("\nLLM配置:")
        print("1. 设置API密钥")
        print("2. 设置API基础URL")
        print("3. 设置默认模型")
        print("4. 返回")
        
        choice = input("请选择 (1-4): ")
        if choice == "1":
            key = input("请输入API密钥: ").strip()
            llm_service.update_setting("api_keys", [key])
        elif choice == "2":
            base = input("请输入API基础URL: ").strip()
            llm_service.update_setting("api_base", base)
        elif choice == "3":
            model = input("请输入模型名称: ").strip()
            llm_service.update_setting("model_name", model)

if __name__ == "__main__":
    interface = ConsoleInterface()
    interface.run()
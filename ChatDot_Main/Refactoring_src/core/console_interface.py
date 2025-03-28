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
        print("4. 管理模型参数")
        print("5. 返回")
        
        choice = input("请选择 (1-5): ")
        if choice == "1":
            key = input("请输入API密钥: ").strip()
            llm_service.update_setting("api_keys", [key])
        elif choice == "2":
            base = input("请输入API基础URL: ").strip()
            llm_service.update_setting("api_base", base)
        elif choice == "3":
            model = input("请输入模型名称: ").strip()
            llm_service.update_setting("model_name", model)
        elif choice == "4":
            self._manage_model_params(llm_service)
    
    def _manage_model_params(self, llm_service):
        """管理模型参数"""
        while True:
            print("\n模型参数管理")
            print("当前参数:")
            current_params = llm_service.settings.get_setting("model_params")
            for key, value in current_params.items():
                print(f"- {key}: {value}")
            
            print("\n操作选项:")
            print("1. 修改参数")
            print("2. 添加新参数")
            print("3. 删除参数")
            print("4. 返回主菜单")
            
            choice = input("\n请选择操作 (1-4): ")
            
            if choice == "1":
                if not current_params:
                    print("当前没有可修改的参数")
                    continue
                    
                print("\n可修改的参数:")
                for i, (key, value) in enumerate(current_params.items(), 1):
                    print(f"{i}. {key}: {value}")
                
                try:
                    idx = int(input("\n请选择要修改的参数编号: ")) - 1
                    if 0 <= idx < len(current_params):
                        key = list(current_params.keys())[idx]
                        current_type = type(current_params[key])
                        new_value = input(f"请输入新的{key}值: ")
                        
                        # 类型转换
                        if current_type == bool:
                            new_value = new_value.lower() in ('true', 'yes', 'y', '1')
                        elif current_type == int:
                            new_value = int(new_value)
                        elif current_type == float:
                            new_value = float(new_value)
                        
                        current_params[key] = new_value
                        llm_service.update_setting("model_params", current_params)
                        print(f"参数 {key} 已更新")
                except (ValueError, IndexError):
                    print("无效的选择")
                    
            elif choice == "2":
                key = input("请输入新参数名称: ").strip()
                if key in current_params:
                    print("参数已存在")
                    continue
                    
                print("\n选择参数类型:")
                print("1. 字符串")
                print("2. 整数")
                print("3. 浮点数")
                print("4. 布尔值")
                
                type_choice = input("请选择参数类型 (1-4): ")
                try:
                    value = input("请输入参数值: ")
                    if type_choice == "2":
                        value = int(value)
                    elif type_choice == "3":
                        value = float(value)
                    elif type_choice == "4":
                        value = value.lower() in ('true', 'yes', 'y', '1')
                        
                    current_params[key] = value
                    llm_service.update_setting("model_params", current_params)
                    print(f"参数 {key} 已添加")
                except ValueError:
                    print("无效的参数值")
                    
            elif choice == "3":
                if not current_params:
                    print("当前没有可删除的参数")
                    continue
                    
                print("\n可删除的参数:")
                for i, key in enumerate(current_params.keys(), 1):
                    print(f"{i}. {key}")
                    
                try:
                    idx = int(input("\n请选择要删除的参数编号: ")) - 1
                    if 0 <= idx < len(current_params):
                        key = list(current_params.keys())[idx]
                        del current_params[key]
                        llm_service.update_setting("model_params", current_params)
                        print(f"参数 {key} 已删除")
                except (ValueError, IndexError):
                    print("无效的选择")
                    
            elif choice == "4":
                break

if __name__ == "__main__":
    interface = ConsoleInterface()
    interface.run()
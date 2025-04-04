from typing import Dict, Callable
from bootstrap import Bootstrap
from global_managers.service_manager import ServiceManager
from global_managers.logger_manager import LoggerManager
import shutil
import sys
import msvcrt
import asyncio
import threading
import time

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
            'live2d': self.configure_live2d,
            'tts': self.configure_tts,
            'stt': self.configure_stt,
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
        print("live2d  - 配置Live2D服务")
        print("tts     - 配置TTS服务")
        print("stt     - 配置STT服务")
        print("exit    - 退出程序")

    def chat_mode(self):
        """进入聊天模式"""
        import asyncio
        import threading
        import time
        
        logger = LoggerManager().get_logger()
        chat_service = self.service_manager.get_service("chat_service")
        context_service = self.service_manager.get_service("context_handle_service")
        stt_service = self.service_manager.get_service("stt_service")
        tts_service = self.service_manager.get_service("tts_service")
        
        #region 界面提示
        print("\n进入聊天模式")
        print("命令选项:")
        print("- 输入 'q' 返回主菜单")
        print("- 输入 'voice' 切换语音/文本输入模式")
        print("- 输入 'open regex' 启用/禁用正则表达式过滤")
        print("- 按 Ctrl+C 停止语音识别或中断生成")
        #endregion
        
        #region 变量定义
        use_filter = False  # 是否启用过滤
        use_voice = False   # 是否使用语音
        recognized_text = ""  # 存储语音识别结果
        #endregion
        
        def on_speech_recognized(text):
            """语音识别回调函数"""
            nonlocal recognized_text
            recognized_text = text
            print(f"\n识别结果: {text}")
            print("按 Ctrl+C 确认使用此输入")
        
        try:
            while True:
                #region 用户输入处理
                if use_voice and stt_service.settings.get_setting("enabled"):
                    try:
                        # 确保TTS已停止播放再开始录音
                        if tts_service and tts_service.is_tts_enabled() and tts_service.is_playing():
                            print("\n等待语音播放完成...")
                            
                            # 等待TTS播放完成或超时
                            wait_start = time.time()
                            while tts_service.is_playing() and (time.time() - wait_start) < 3:
                                time.sleep(0.1)
                            
                            # 如果仍在播放，强制停止
                            if tts_service.is_playing():
                                print("强制停止当前语音播放")
                                tts_service.stop_playing()
                                time.sleep(0.5)  # 短暂等待确保完全停止
                        
                        recognized_text = ""
                        
                        # 创建事件循环
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        print("\n语音输入模式已启用，请说话...")
                        print("按 Ctrl+C 停止识别并提交文本")
                        
                        # 初始化并启动STT服务
                        async def start_stt():
                            if not await stt_service.initialize_async():
                                logger.error("STT服务初始化失败")
                                return False
                            
                            # 清除回调并设置新回调
                            stt_service.segment_callbacks = []
                            stt_service.add_segment_callback(on_speech_recognized)
                            
                            # 启动识别
                            if not await stt_service.start_recognition_async():
                                logger.error("启动语音识别失败")
                                return False
                            
                            return True
                        
                        try:
                            success = loop.run_until_complete(start_stt())
                            if not success:
                                print("语音输入初始化失败，切换回文本输入模式")
                                use_voice = False
                                user_input = input("\n用户: ")
                            else:
                                try:
                                    # 运行事件循环，等待Ctrl+C中断
                                    loop.run_forever()
                                except KeyboardInterrupt:
                                    print("\n语音识别已停止")
                                finally:
                                    # 确保STT服务被停止
                                    loop.run_until_complete(stt_service.stop_recognition_async())
                                
                                # 如果有识别结果，则提交
                                if recognized_text:
                                    user_input = recognized_text
                                else:
                                    print("\n未检测到有效输入，请重试或输入 'q' 返回主菜单")
                                    user_input = input("\n用户: ")
                        except Exception as e:
                            logger.error(f"语音识别处理错误: {e}")
                            print("\n语音识别处理出错，切换到文本输入")
                            user_input = input("\n用户: ")
                        finally:
                            # 关闭事件循环
                            loop.close()
                            
                    except Exception as e:
                        logger.error(f"语音识别错误: {e}")
                        print("\n语音识别出错，切换到文本输入")
                        user_input = input("\n用户: ")
                else:
                    # 文本输入模式
                    user_input = input("\n用户: ")
                #endregion
                    
                #region 命令处理
                if user_input.lower() == 'q':
                    break
                elif user_input.lower() == 'voice':
                    use_voice = not use_voice
                    mode_str = "已启用" if use_voice else "已禁用"
                    print(f"语音输入模式 {mode_str}")
                    
                    # 如果启用语音但STT服务未启用，提示用户
                    if use_voice and not stt_service.settings.get_setting("enabled"):
                        print("警告: STT服务未启用，请先在STT配置中启用")
                        print("您可以退出聊天模式，使用'stt'命令进行配置")
                    continue
                elif user_input.lower() == "open regex":
                    use_filter = not use_filter
                    mode_str = "已启用" if use_filter else "已禁用"
                    print(f"正则表达式过滤 {mode_str}")
                    continue
                elif not user_input.strip():
                    continue
                #endregion
                
                #region 消息处理与响应显示
                try:
                    # 先停止所有正在播放的TTS音频
                    if tts_service and tts_service.is_tts_enabled():
                        tts_service.stop_playing()
                    
                    # 获取原始响应（TTS处理已经在ChatClient中完成）
                    response_iterator = chat_service.send_message(user_input, is_stream=True)
                    
                    # 处理响应（仅显示，无需重复TTS处理）
                    try:
                        if not use_filter:
                            #region 标准输出处理
                            try:
                                first_chunk = next(response_iterator)
                                print("助手: " + first_chunk, end='', flush=True)
                                
                                # 显示剩余响应
                                for chunk in response_iterator:
                                    print(chunk, end='', flush=True)
                                print()  # 换行
                            except StopIteration:
                                print("助手: ", end='', flush=True)
                                print()  # 空响应
                            #endregion
                        else:
                            #region 过滤模式处理
                            accumulated_text = ""
                            chunk_count = 0
                            
                            for chunk in response_iterator:
                                accumulated_text += chunk
                                chunk_count += 1
                                
                                processed_text = context_service.get_current_handler().process_before_show(accumulated_text)
                                print(f"[chunk {chunk_count}] {processed_text}")
                            #endregion
                    except KeyboardInterrupt:
                        print("\n[已打断]")
                        chat_service.stop_generating()
                        if tts_service and tts_service.is_tts_enabled():
                            tts_service.stop_playing()
                except Exception as e:
                    logger.error(f"处理响应错误: {e}")
                    print("\n处理响应时出错")
                #endregion
        except KeyboardInterrupt:
            print("\n退出聊天模式")
        finally:
            #region 资源清理
            # 停止TTS
            if tts_service and tts_service.is_tts_enabled():
                tts_service.stop_playing()
            
            # 关闭STT服务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(stt_service.shutdown_async())
            loop.close()
            #endregion    
  
    # def chat_mode(self):
    #     """进入聊天模式"""
    #     chat_service = self.service_manager.get_service("chat_service")
    #     context_service = self.service_manager.get_service("context_handle_service")
    #     print("\n进入聊天模式 (输入 'q' 返回主菜单，输入'open regex'启用正则表达式过滤)")
        
    #     # 默认不启用过滤
    #     use_filter = False
            
    #     while True:
    #         user_input = input("\n用户: ")
    #         if user_input.lower() == 'q':
    #             break
                
    #         # 检查是否切换过滤模式
    #         if user_input.lower() == "open regex":
    #             use_filter = not use_filter
    #             mode_str = "已启用" if use_filter else "已禁用"
    #             print(f"正则表达式过滤 {mode_str}")
    #             continue
            
    #         try:
    #             if not use_filter:
    #                 # 不过滤，直接流式输出
    #                 response_iterator = chat_service.send_message(user_input, is_stream=True)
    #                 # 等待第一个响应后再打印"助手: "
    #                 first_chunk = next(response_iterator)
    #                 print("助手: " + first_chunk, end='', flush=True)
    #                 for chunk in response_iterator:
    #                     # 检查是否按下 ESC 键
    #                     if msvcrt.kbhit() and msvcrt.getch() == b'\x1b':
    #                         chat_service.stop_generating()
    #                         print("\n[已打断]", end='', flush=True)
    #                         break
    #                     print(chunk, end='', flush=True)
    #                 print()  # 打印换行
    #             else:
    #                 # 启用过滤，显示处理后的完整文本
    #                 accumulated_text = ""
    #                 chunk_count = 0
    #                 response_iterator = chat_service.send_message(user_input, is_stream=True)
                    
    #                 for chunk in response_iterator:
    #                     # 检查是否按下 ESC 键
    #                     if msvcrt.kbhit() and msvcrt.getch() == b'\x1b':
    #                         chat_service.stop_generating()
    #                         print("\n[已打断]")
    #                         break
                        
    #                     accumulated_text += chunk
    #                     chunk_count += 1
                        
    #                     # 处理完整文本并打印
    #                     processed_text = context_service.get_current_handler().process_before_show(accumulated_text)
    #                     print(f"[chunk {chunk_count}] {processed_text}")
                        
    #         except Exception as e:
    #             print(f"\n错误: {str(e)}")

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


    #region 配置 Live2D 服务
    def configure_live2d(self):
        """配置 Live2D 服务"""
        live2d_service = self.service_manager.get_service("live2d_service")
        
        print("\nLive2D 配置:")
        print("1. 启用/禁用 Live2D")
        print("2. 设置 Live2D URL")
        print("3. 返回主菜单")
        
        choice = input("请选择 (1-3): ").strip()
        if choice == "1":
            current_status = live2d_service.settings.get_setting("initialize")
            new_status = not current_status
            live2d_service.update_setting("initialize", new_status)
            status_str = "启用" if new_status else "禁用"
            print(f"Live2D 已{status_str}")
        elif choice == "2":
            new_url = input("请输入新的 Live2D URL: ").strip()
            live2d_service.update_setting("url", new_url)
            print(f"Live2D URL 已更新为: {new_url}")
        elif choice == "3":
            return
        else:
            print("无效的选择，请重试")
    #endregion
    
    #region 配置 TTS 服务
    def configure_tts(self):
        """配置 TTS 服务"""
        tts_service = self.service_manager.get_service("tts_service")
        
        while True:
            print("\nTTS 配置:")
            print("1. 启用/禁用 TTS")
            print("2. 设置 TTS URL")
            print("3. 配置流式模式")
            print("4. 配置语音参数")
            print("5. 管理预设角色")
            print("6. 测试 TTS")
            print("7. 返回主菜单")
            
            choice = input("请选择 (1-7): ").strip()
            
            if choice == "1":
                current_status = tts_service.settings.get_setting("initialize")
                new_status = not current_status
                tts_service.update_setting("initialize", new_status)
                status_str = "启用" if new_status else "禁用"
                print(f"TTS 已{status_str}")
                
            elif choice == "2":
                new_url = input("请输入新的 TTS URL (例如: http://183.175.12.68:9880): ").strip()
                tts_service.update_setting("url", new_url)
                print(f"TTS URL 已更新为: {new_url}")
                
            elif choice == "3":
                current_mode = tts_service.settings.get_setting("streaming_mode")
                new_mode = not current_mode
                mode_str = "启用" if new_mode else "禁用"
                tts_service.update_setting("streaming_mode", new_mode)
                print(f"流式模式已{mode_str}")
                
            elif choice == "4":
                self._configure_tts_params(tts_service)
                
            elif choice == "5":
                self._manage_tts_presets(tts_service)
                
            elif choice == "6":
                self._test_tts(tts_service)
                
            elif choice == "7":
                break
                
            else:
                print("无效的选择，请重试")

    def _configure_tts_params(self, tts_service):
        """配置 TTS 详细参数"""
        print("\nTTS 参数配置:")
        print("1. 设置文本语言")
        print("2. 设置参考音频路径")
        print("3. 设置提示语言")
        print("4. 设置提示文本")
        print("5. 设置文本分割方法")
        print("6. 设置批处理大小")
        print("7. 设置媒体类型")
        print("8. 更换sovits模型")
        print("9. 返回")
        
        choice = input("请选择 (1-8): ").strip()
        
        if choice == "1":
            current = tts_service.settings.get_setting("text_lang")
            new_value = input(f"请输入文本语言 (当前: {current}): ").strip() or current
            tts_service.update_setting("text_lang", new_value)
            
        elif choice == "2":
            current = tts_service.settings.get_setting("ref_audio_path")
            new_value = input(f"请输入参考音频路径 (当前: {current}): ").strip() or current
            tts_service.update_setting("ref_audio_path", new_value)
            
        elif choice == "3":
            current = tts_service.settings.get_setting("prompt_lang")
            new_value = input(f"请输入提示语言 (当前: {current}): ").strip() or current
            tts_service.update_setting("prompt_lang", new_value)
            
        elif choice == "4":
            current = tts_service.settings.get_setting("prompt_text")
            new_value = input(f"请输入提示文本 (当前: {current}): ").strip() or current
            tts_service.update_setting("prompt_text", new_value)
            
        elif choice == "5":
            current = tts_service.settings.get_setting("text_split_method")
            new_value = input(f"请输入文本分割方法 (当前: {current}): ").strip() or current
            tts_service.update_setting("text_split_method", new_value)
            
        elif choice == "6":
            current = tts_service.settings.get_setting("batch_size")
            try:
                new_value = int(input(f"请输入批处理大小 (当前: {current}): ").strip() or current)
                tts_service.update_setting("batch_size", new_value)
            except ValueError:
                print("输入无效，需要整数值")
            
        elif choice == "7":
            current = tts_service.settings.get_setting("media_type")
            new_value = input(f"请输入媒体类型 (当前: {current}): ").strip() or current
            tts_service.update_setting("media_type", new_value)
        elif choice == "8":
            current = tts_service.settings.get_setting("sovits_model_path")
            new_value = input(f"请输入新的sovits模型路径 (当前: {current}): ").strip() or current
            tts_service.update_setting("sovits_model_path", new_value)
        elif choice == "9":
            return
        else:
            print("无效的选择")

    def _test_tts(self, tts_service):
        """测试 TTS 功能"""
        if not tts_service.is_tts_enabled():
            print("TTS 服务未启用，请先启用")
            return
            
        test_text = input("请输入要合成的文本 (默认: 这是一个TTS测试): ").strip()
        if not test_text:
            test_text = "这是一个TTS测试"
        
        print(f"正在合成文本: {test_text}")
        try:
            tts_service.play_text_to_speech(test_text)
            print("音频播放完成")
        except Exception as e:
            print(f"TTS 测试失败: {e}")
    #endregion


    def _manage_tts_presets(self, tts_service):
        """管理 TTS 预设角色"""
        while True:
            presets = tts_service.get_all_presets()
            current_preset_id = tts_service.settings.get_setting("current_preset")  # 直接获取当前预设ID
            current_preset = tts_service.get_preset(current_preset_id)  # 获取当前预设详情
            
            print("\n=== 预设角色管理 ===")
            print(f"当前使用的预设: {current_preset_id}")
            print(f"预设名称: {current_preset['name'] if current_preset else '无'}")
            print("\n可用的预设角色:")
            for preset_id, preset_data in presets.items():
                print(f"- {preset_id}: {preset_data['name']}")
            
            
            print("\n操作选项:")
            print("1. 切换预设")
            print("2. 查看预设详情")
            print("3. 添加新预设")
            print("4. 删除预设")
            print("5. 返回")
            
            choice = input("\n请选择操作 (1-5): ").strip()
            
            if choice == "1":
                preset_id = input("请输入要切换的预设ID: ").strip()
                result = tts_service.switch_preset(preset_id)
                if isinstance(result, dict) and "error" in result:
                    print(f"切换失败: {result['error']}")
                else:
                    print(f"已成功切换到预设: {preset_id}")
                    
            elif choice == "2":
                preset_id = input("请输入要查看的预设ID: ").strip()
                preset = tts_service.get_preset(preset_id)
                if preset:
                    print(f"\n预设 '{preset_id}' 的详细信息:")
                    for key, value in preset.items():
                        print(f"{key}: {value}")
                else:
                    print("预设不存在")
                    
            elif choice == "3":
                preset_id = input("请输入新预设ID (仅允许英文和数字): ").strip()
                if not preset_id.isalnum():
                    print("预设ID只能包含英文字母和数字")
                    continue
                    
                if preset_id in presets:
                    print("预设ID已存在")
                    continue
                    
                print("\n请输入预设信息:")
                new_preset = {
                    "name": input("角色名称: ").strip(),
                    "ref_audio_path": input("参考音频路径: ").strip(),
                    "prompt_text": input("提示文本: ").strip(),
                    "text_lang": input("文本语言 (如 zh): ").strip() or "zh",
                    "prompt_lang": input("提示语言 (如 zh): ").strip() or "zh",
                    "gpt_weights_path": input("GPT模型权重路径: ").strip(),
                    "sovits_weights_path": input("Sovits模型权重路径: ").strip(),
                    "text_split_method": "cut5",  # 默认值
                    "batch_size": 1,              # 默认值
                    "media_type": "wav",          # 默认值
                    "streaming_mode": True         # 默认值
                }
                
                # 检查必填字段
                required_fields = ["name", "ref_audio_path", "prompt_text", "gpt_weights_path", "sovits_weights_path"]
                if all(new_preset[field] for field in required_fields):
                    if tts_service.add_preset(preset_id, new_preset):
                        print(f"预设 '{preset_id}' 添加成功")
                    else:
                        print("添加预设失败")
                else:
                    print("必填字段不能为空")
                    
            elif choice == "4":
                preset_id = input("请输入要删除的预设ID: ").strip()
                current = tts_service.get_preset()
                if preset_id == "default":
                    print("不能删除默认预设")
                elif current and preset_id == current.get("name"):
                    print("不能删除当前正在使用的预设")
                elif tts_service.remove_preset(preset_id):
                    print(f"预设 '{preset_id}' 已成功删除")
                else:
                    print("删除预设失败")
                    
            elif choice == "5":
                break
            
            else:
                print("无效的选择，请重试")
                
            # 操作后暂停一下
            input("\n按回车键继续...")

    def configure_stt(self):
        """配置STT(语音转文本)服务"""
        # 获取STT服务
        stt_service = self.service_manager.get_service("stt_service")
        
        # 检查是否有可用的麦克风
        if not self._check_available_microphone():
            print("错误: 未检测到可用的麦克风设备，无法使用STT功能")
            return
        
        while True:
            print("\nSTT配置:")
            print("1. 在聊天中启用/禁用STT")
            print("2. 配置STT服务器设置")
            print("3. 测试STT功能")
            print("4. 返回主菜单")
            
            choice = input("请选择 (1-4): ").strip()
            
            if choice == "1":
                self._toggle_stt_in_chat(stt_service)
            elif choice == "2":
                self._configure_stt_server(stt_service)
            elif choice == "3":
                self._test_stt(stt_service)
            elif choice == "4":
                break
            else:
                print("无效的选择，请重试")

    def _check_available_microphone(self):
        """检查是否有可用的麦克风设备"""
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            input_devices = 0
            
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                if device_info.get('maxInputChannels') > 0:
                    input_devices += 1
                    
            p.terminate()
            return input_devices > 0
        except Exception as e:
            print(f"检查麦克风设备时出错: {e}")
            return False

    def _toggle_stt_in_chat(self, stt_service):
        """启用或禁用聊天中的STT功能"""
        # 获取当前状态
        current_status = stt_service.settings.get_setting("enabled")
        new_status = not current_status
        
        # 更新设置
        stt_service.settings.update_setting("enabled", new_status)
        status_str = "启用" if new_status else "禁用"
        print(f"聊天中的STT功能已{status_str}")
        
        # 保存配置
        stt_service.save_config()

    def _configure_stt_server(self, stt_service):
        """配置STT服务器设置"""
        print("\nSTT服务器配置:")
        
        # 获取当前设置
        current_host = stt_service.settings.get_setting("host")
        current_port = stt_service.settings.get_setting("port")
        current_local = stt_service.settings.get_setting("use_local_server")
        current_auto = stt_service.settings.get_setting("auto_start_server")
        
        print(f"当前设置:")
        print(f"- 服务器地址: {current_host}")
        print(f"- 服务器端口: {current_port}")
        print(f"- 使用本地服务器: {current_local}")
        print(f"- 自动启动服务器: {current_auto}")
        
        # 选择服务器类型
        server_choice = input("\n选择服务器类型:\n1. 本地服务器 (localhost)\n2. 远程服务器\n请输入选择 (默认1): ")
        
        if server_choice == "2":
            # 配置远程服务器
            host = input(f"请输入服务器地址 (当前: {current_host}): ").strip() or current_host
            port = input(f"请输入服务器端口 (当前: {current_port}): ").strip()
            
            try:
                port = int(port) if port else current_port
                stt_service.update_server_config(
                    host=host, 
                    port=port,
                    use_local_server=False
                )
                print(f"服务器设置已更新: {host}:{port} (远程服务器)")
            except ValueError:
                print("端口必须是数字")
        else:
            # 配置本地服务器
            port = input(f"请输入服务器端口 (当前: {current_port}): ").strip()
            auto_start = input(f"是否自动启动服务器 (y/n, 当前: {'y' if current_auto else 'n'}): ").strip().lower()
            
            try:
                port = int(port) if port else current_port
                auto_start = auto_start in ('y', 'yes', 'true', '1') if auto_start else current_auto
                
                stt_service.update_server_config(
                    host="localhost", 
                    port=port,
                    use_local_server=True,
                    auto_start_server=auto_start
                )
                print(f"服务器设置已更新: localhost:{port} (本地服务器, 自动启动: {auto_start})")
            except ValueError:
                print("端口必须是数字")

    def _test_stt(self, stt_service):
        """测试STT功能"""
        try:
            print("\n开始STT测试...")
            print("正在初始化STT服务...")
            
            # 获取或创建事件循环
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    print("检测到正在运行的事件循环，无法启动测试")
                    return
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if not loop.run_until_complete(stt_service.initialize_async()):
                print("STT服务初始化失败，请检查配置")
                return
            
            # 定义识别回调
            def segment_callback(text):
                print(f"\n识别结果: {text}")
                
            stt_service.add_segment_callback(segment_callback)
            
            # 启动识别
            if not loop.run_until_complete(stt_service.start_recognition_async()):
                print("启动语音识别失败")
                return
            
            print("\n开始语音识别，请说话...")
            print("按'q'退出测试")
            
            # 等待用户按q退出
            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode().lower()
                    if key == 'q':
                        break
                time.sleep(0.1)
                    
        except Exception as e:
            print(f"测试过程中出错: {e}")
        finally:
            # 确保服务被正确关闭
            try:
                # 停止识别并关闭服务
                print("\n关闭服务...")
                if 'loop' in locals() and not loop.is_closed():
                    loop.run_until_complete(stt_service.stop_recognition_async())
                    loop.run_until_complete(stt_service.shutdown_async())
                    # 不要关闭主事件循环
                    if loop != asyncio.get_event_loop():
                        loop.close()
                print("STT测试已停止")
            except Exception as e:
                print(f"关闭服务时出错: {e}")
                
if __name__ == "__main__":
    interface = ConsoleInterface()
    interface.run()
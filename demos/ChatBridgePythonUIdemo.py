import asyncio
import websockets
import json
import tkinter as tk
from tkinter import ttk
import threading

class STServer:
    def __init__(self, port=8001):
        self.port = port
        self.host = "localhost"
        self.connected_clients = set()
        self.stream_prefix_displayed = False
        self.server = None
        self.server_task = None
        self.loop = None
        self.loop_thread = None
        self.setup_gui()
        self.setup_chat_display()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("ST Bridge Python Controller")

        # 服务器设置框架
        self.server_frame = ttk.LabelFrame(self.root, text="服务器设置", padding="5")
        self.server_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        # 地址和端口输入
        ttk.Label(self.server_frame, text="地址:").grid(row=0, column=0, sticky=tk.W)
        self.host_var = tk.StringVar(value=self.host)
        self.host_entry = ttk.Entry(self.server_frame, textvariable=self.host_var, width=20)
        self.host_entry.grid(row=0, column=1, padx=5)

        ttk.Label(self.server_frame, text="端口:").grid(row=0, column=2, sticky=tk.W)
        self.port_var = tk.StringVar(value=str(self.port))
        self.port_entry = ttk.Entry(self.server_frame, textvariable=self.port_var, width=10)
        self.port_entry.grid(row=0, column=3, padx=5)

        # 启动按钮
        self.start_button = ttk.Button(self.server_frame, text="启动服务器", command=self.start_stop_server)
        self.start_button.grid(row=0, column=4, padx=5)

        # 消息输入区域
        self.message_frame = ttk.LabelFrame(self.root, text="消息控制", padding="5")
        self.message_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        self.message_var = tk.StringVar()
        self.message_entry = ttk.Entry(self.message_frame, textvariable=self.message_var, width=40)
        self.message_entry.grid(row=0, column=0, padx=5)

        self.send_button = ttk.Button(self.message_frame, text="发送", command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=5)
        self.send_button.state(['disabled'])

        # 聊天记录显示
        self.setup_chat_display()

        # 日志显示
        self.log_frame = ttk.LabelFrame(self.root, text="日志", padding="5")
        self.log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        self.log_text = tk.Text(self.log_frame, height=10, width=50)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.server_running = False

    def setup_chat_display(self):
        self.chat_frame = ttk.LabelFrame(self.root, text="聊天记录", padding="5")
        self.chat_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        self.chat_text = tk.Text(self.chat_frame, height=15, width=50)
        self.chat_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.chat_scroll = ttk.Scrollbar(self.chat_frame, orient="vertical", command=self.chat_text.yview)
        self.chat_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.chat_text.configure(yscrollcommand=self.chat_scroll.set)

    def update_chat_display(self, chat_history):
        self.chat_text.delete('1.0', tk.END)
        for message in chat_history:
            name = message.get('name', 'Unknown')
            content = message.get('mes', '')
            self.chat_text.insert(tk.END, f"{name}: {content}\n\n")
        self.chat_text.see(tk.END)

    def update_stream_display(self, content):
        try:
            if not self.stream_prefix_displayed:
                # 如果还没有显示前缀，则添加前缀并插入内容
                self.chat_text.insert("end-1c", f"Assistant(生成中): {content}")
                self.stream_prefix_displayed = True
                self.chat_text.see("end")
            else:
                # 如果已经显示前缀，则只追加内容
                self.chat_text.insert("end-1c", content)
                self.chat_text.see("end")
        except Exception as e:
            self.update_log(f"更新流式显示错误: {str(e)}")

    def update_log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)

    def send_message(self):
        message = self.message_var.get()
        if message and self.connected_clients:
            asyncio.run_coroutine_threadsafe(self.broadcast_message(message), self.loop)
            self.message_var.set("")
            self.update_log(f"发送消息: {message}")

    def start_stop_server(self):
        if not self.server_running:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        self.host = self.host_var.get()
        self.port = int(self.port_var.get())
        self.host_entry.state(['disabled'])
        self.port_entry.state(['disabled'])
        self.start_button.configure(text="停止服务器")
        self.send_button.state(['!disabled'])
        self.server_running = True

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.server_task = self.loop.create_task(self._start_server())
        self.loop_thread = threading.Thread(target=self.run_loop, daemon=True)
        self.loop_thread.start()

    def stop_server(self):
        self.update_log("停止服务器...")
        self.host_entry.state(['!disabled'])
        self.port_entry.state(['!disabled'])
        self.start_button.configure(text="启动服务器")
        self.send_button.state(['disabled'])
        self.server_running = False

        if self.server_task:
            asyncio.run_coroutine_threadsafe(self.cancel_server_task(), self.loop)

    def run_loop(self):
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()

    async def cancel_server_task(self):
        self.update_log("取消服务器任务...")
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                self.update_log("服务器任务已取消")
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.update_log("服务器已关闭")
        self.loop.stop()
        self.update_log("事件循环已停止")

    async def _start_server(self):
        try:
            self.server = await websockets.serve(self.handle_client, self.host, self.port)
            self.update_log(f"WebSocket服务器运行在 ws://{self.host}:{self.port}")
            await self.server.wait_closed()
        except asyncio.CancelledError:
            self.update_log("服务器被取消")
        except Exception as e:
            self.update_log(f"服务器发生错误: {e}")
        finally:
            self.update_log("服务器停止")

    async def broadcast_message(self, content):
        if not self.connected_clients:
            self.update_log("没有连接的客户端")
            return

        message = {
            "type": "send_message",
            "content": content
        }

        for client in self.connected_clients:
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                self.connected_clients.remove(client)

    async def handle_client(self, websocket):
        self.connected_clients.add(websocket)
        self.update_log(f"新客户端连接: {websocket.remote_address}")

        try:
            async for message in websocket:
                data = json.loads(message)
                self.update_log(f"收到消息类型: {data['type']}")

                if data['type'] == 'chat_history':
                    self.root.after(0, lambda: self.update_chat_display(data['content']))
                elif data['type'] == 'stream_update':
                    content = data.get('content', '')
                    self.root.after(0, lambda c=content: self.update_stream_display(c))
        except Exception as e:
            self.update_log(f"错误: {str(e)}")
        finally:
            self.connected_clients.remove(websocket)
            self.update_log("客户端断开连接")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    server = STServer()
    server.run()
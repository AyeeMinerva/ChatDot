import socket
import threading
import json

class ProcessCommunicator:
    _instance = None

    def __init__(self, is_server, host='127.0.0.1', port=5000):
        if ProcessCommunicator._instance is not None:
            raise Exception("请使用 ProcessCommunicator.instance() 获取单例")
        self.is_server = is_server
        self.host = host
        self.port = port
        self.sock = None
        self._active = False
        self.status = "未初始化"
        self.clients = {}  # client_id: conn
        self.recv_threads = {}
        self.lock = threading.Lock()
        self.conn = None  # 客户端模式下使用
        self.topic_handlers = {}  # 主题前缀: 回调函数

    @classmethod
    def instance(cls, is_server=None, host='127.0.0.1', port=5000):
        if cls._instance is None:
            if is_server is None:
                raise Exception("首次调用必须指定 is_server")
            cls._instance = cls(is_server, host, port)
        return cls._instance

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value: bool):
        if value and not self._active:
            self._active = True
            self._init_connection()
        elif not value and self._active:
            self._active = False
            self._close_connection()

    def _init_connection(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.is_server:
                self.sock.bind((self.host, self.port))
                self.sock.listen(5)
                self.status = f"服务器监听中 {self.host}:{self.port}"
                threading.Thread(target=self._accept_clients, daemon=True).start()
            else:
                self.sock.connect((self.host, self.port))
                self.conn = self.sock
                self.status = f"已连接到服务器 {self.host}:{self.port}"
                t = threading.Thread(target=self._receive_client, args=(self.conn,), daemon=True)
                t.start()
        except Exception as e:
            self.status = f"初始化失败: {e}"
            self._active = False

    def _accept_clients(self):
        while self._active:
            try:
                conn, addr = self.sock.accept()
                client_id = f"{addr[0]}:{addr[1]}"
                with self.lock:
                    self.clients[client_id] = conn
                self.status = f"已连接: {client_id}"
                t = threading.Thread(target=self._receive_server, args=(conn, client_id), daemon=True)
                self.recv_threads[client_id] = t
                t.start()
            except Exception as e:
                self.status = f"接受客户端异常: {e}"
                break

    def _close_connection(self):
        try:
            if self.is_server:
                with self.lock:
                    for conn in self.clients.values():
                        conn.close()
                    self.clients.clear()
            else:
                if self.conn:
                    self.conn.close()
            if self.sock:
                self.sock.close()
            self.status = "已关闭"
        except Exception as e:
            self.status = f"关闭异常: {e}"
        self.conn = None
        self.sock = None

    def send(self, msg: str, topic: str):
        if not self._active:
            self.status = "未连接，无法发送"
            return
        try:
            data = {"msg": msg, "topic": topic}
            if self.is_server:
                with self.lock:
                    for conn in self.clients.values():
                        conn.sendall(json.dumps(data).encode('utf-8'))
            else:
                if self.conn:
                    self.conn.sendall(json.dumps(data).encode('utf-8'))
        except Exception as e:
            self.status = f"发送失败: {e}"

    def add_handler(self, prefix: str, handler):
        """注册主题前缀对应的回调函数，handler(msg: dict, topic: str)"""
        self.topic_handlers[prefix] = handler

    def _dispatch_message(self, msg, topic):
        # 匹配所有“此主题本身”及“此主题的子主题”的handler，全部调用
        for prefix, handler in self.topic_handlers.items():
            if prefix == "" or topic == prefix or topic.startswith(prefix + "."):
                handler(msg, topic)

    def _receive_server(self, conn, client_id):
        while self._active:
            try:
                data = conn.recv(1024)
                if not data:
                    self.status = f"客户端断开"
                    break
                msg = json.loads(data.decode('utf-8'))
                topic = msg.get("topic", "")
                print(f"\n收到消息: {msg}")
                # 广播给所有其他客户端
                with self.lock:
                    for cid, cconn in self.clients.items():
                        if cid != client_id:
                            try:
                                cconn.sendall(json.dumps(msg).encode('utf-8'))
                            except Exception:
                                pass  # 忽略单个客户端异常
                # 本地分发（服务器本地handler）
                self._dispatch_message(msg, topic)
            except Exception as e:
                self.status = f"接收异常: {e}"
                break

    def _receive_client(self, conn):
        while self._active:
            try:
                data = conn.recv(1024)
                if not data:
                    self.status = "服务器断开"
                    self.active = False
                    break
                msg = json.loads(data.decode('utf-8'))
                topic = msg.get("topic", "")
                print(f"\n收到消息: {msg}")
                self._dispatch_message(msg, topic)
            except Exception as e:
                self.status = f"接收异常: {e}"
                self.active = False
                break

if __name__ == "__main__":
    mode = input("输入's'作为服务器，输入'c'作为客户端: ").strip().lower()
    is_server = mode == 's'
    app = ProcessCommunicator.instance(is_server)
    app.active = True
    print("输入内容发送消息，输入/exit退出")
    while app.active:
        msg = input("输入消息内容: ")
        if msg == "/exit":
            app.active = False
            break
        topic = input("输入topic标志: ")
        app.send(msg, topic)
    print("程序已退出")

"""
外部调用方法说明：

1. 引入ProcessCommunicator类
   from chat_app import ProcessCommunicator

2. 获取单例实例（首次需指定is_server）
   app = ProcessCommunicator.instance(is_server=True)  # 作为服务器
   # 或
   app = ProcessCommunicator.instance(is_server=False) # 作为客户端

3. 启动或关闭连接
   app.active = True   # 启动
   app.active = False  # 关闭

4. 发送消息
   app.send("消息内容", "topic.abc")  # topic为字符串类型

5. 注册不同topic前缀的回调（支持多匹配，topic为空字符串视为全局回调）
   def tts_a_handler(msg: dict, topic: str):
       print("处理tts.a相关消息:", msg)
   def tts_handler(msg: dict, topic: str):
       print("处理tts及其子主题相关消息:", msg)
   def global_handler(msg: dict, topic: str):
       print("全局消息:", msg)
   app.add_handler('tts.a', tts_a_handler)
   app.add_handler('tts', tts_handler)
   app.add_handler('', global_handler)  # 注册全局回调（topic为空字符串）

   # 说明：
   # - 收到消息时，所有匹配“此主题本身”及“此主题的子主题”的handler都会被调用
   # - handler的标准写法：def handler(msg: dict, topic: str):

6. 示例：完整注册流程
   app = ProcessCommunicator.instance(is_server=False)
   def tts_a_handler(msg, topic):
       print("收到tts.a及其子主题消息:", msg)
   def global_handler(msg, topic):
       print("收到全局消息:", msg)
   app.add_handler('tts.a', tts_a_handler)
   app.add_handler('', global_handler)
   app.active = True
   app.send("hello", "tts.a.b")
"""

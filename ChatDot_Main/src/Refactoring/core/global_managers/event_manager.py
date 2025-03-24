class EventManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EventManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.events = {}
        return cls._instance

    def register_event(self, event_name):
        """注册一个新的事件"""
        if event_name not in self.events:
            self.events[event_name] = []

    def subscribe(self, event_name, listener):
        """订阅一个事件"""
        if event_name not in self.events:
            raise ValueError(f"事件 '{event_name}' 未注册。")
        self.events[event_name].append(listener)

    def unsubscribe(self, event_name, listener):
        """取消订阅一个事件"""
        if event_name in self.events and listener in self.events[event_name]:
            self.events[event_name].remove(listener)

    def emit(self, event_name, *args, **kwargs):
        """触发一个事件"""
        if event_name not in self.events:
            raise ValueError(f"事件 '{event_name}' 未注册。")
        for listener in self.events[event_name]:
            listener(*args, **kwargs)
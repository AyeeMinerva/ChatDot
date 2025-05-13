import logging
import sys
import threading

#替换print用的正则表达式
#查找：print\((.*?)\)
#替换为：logger.debug(\1)

class LoggerManager:
    _instance = None
    _lock = threading.Lock()  # 确保线程安全

    def __new__(cls, *args, **gkwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(LoggerManager, cls).__new__(cls)
                    cls._instance._loggers = {}
        return cls._instance

    def get_logger(self, name=None, level=logging.DEBUG):
        """
        获取一个logger实例。如果未指定名称，则自动识别调用者模块名称。
        :param name: 日志名称（可选）
        :param level: 日志级别
        :return: logger实例
        """
        if not name:
            # 自动获取调用者模块的名称
            frame = sys._getframe(1)
            name = frame.f_globals.get("__name__", "unknown")

        if name not in self._loggers:
            # 创建新的logger
            logger = logging.getLogger(name)
            logger.setLevel(level)

            # 如果logger没有处理器，则添加控制台处理器
            if not logger.handlers:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)

            self._loggers[name] = logger

        return self._loggers[name]
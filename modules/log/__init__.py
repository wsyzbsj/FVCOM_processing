import pathlib
import logging
import sys

class AppLogger:
    def __init__(self, name, log_level:str, logpath:pathlib.Path): #初始化
        """
        :param name: 日志记录器名称
        :param log_level: 默认日志级别 level_name (str): 日志级别名称 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        :param logpath: 日志文件目录
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        # 确保只添加一个控制台处理程序
        self.console_handler = None
        # 初始化基础配置
        self._setup_base_config()
        self.add_file_handler(file_path=logpath, level=log_level)

    def _setup_base_config(self):
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler) # 移除所有现有处理程序
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s') # 格式化输出log
        # 创建并配置控制台处理程序
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setFormatter(formatter)
        self.logger.addHandler(self.console_handler)

    def add_file_handler(self, file_path, level=None): # 添加文件日志处理程序
        file_handler = logging.FileHandler(file_path)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s')
        file_handler.setFormatter(file_formatter)

        if level:
            file_handler.setLevel(getattr(logging, level, logging.INFO))

        self.logger.addHandler(file_handler)
        self.logger.info("添加文件日志处理程序: %s", file_path)

    def __getattr__(self, name):
        # 将未定义的属性调用转发给self.logger
        return getattr(self.logger, name)
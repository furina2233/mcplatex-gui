"""
Qt日志桥接工具类
用于将Rich Console输出桥接到Qt信号，实现后端日志与前端UI的同步
"""
from PySide6.QtCore import QObject, Signal


class QtConsoleBridge(QObject):
    """
    Rich Console到Qt信号的桥接器
    提供一个类似Console的接口，但会将所有输出通过Qt信号发射
    """
    log_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buffer = []

    def print(self, *objects, sep=' ', end='\n', **kwargs):
        """
        模拟Console的print方法，将输出通过信号发射
        支持Rich的格式化字符串（会移除标记）
        """
        # 将所有对象转换为字符串并拼接
        text = sep.join(str(obj) for obj in objects) + end

        # 移除Rich的ANSI颜色标记（如果有的话）
        # 简单实现：移除方括号标记如 [bold], [green] 等
        import re
        # 移除Rich格式标记，但保留方括号内容
        cleaned_text = re.sub(r'\[/?[a-z][a-z0-9_]*\]', '', text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\[link=[^\]]*\]', '', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\[/link\]', '', cleaned_text, flags=re.IGNORECASE)

        # 发射信号
        if cleaned_text.strip():
            self.log_message.emit(cleaned_text.rstrip())

    def rule(self, title='', character='─', style='', **kwargs):
        """
        模拟Console的rule方法，输出分隔线
        """
        import re
        # 移除Rich格式标记
        cleaned_title = re.sub(r'\[/?[a-z][a-z0-9_]*\]', '', str(title), flags=re.IGNORECASE)

        rule_text = f"{'─' * 10} {cleaned_title} {'─' * 10}" if cleaned_title else character * 30
        self.log_message.emit(rule_text)

    def flush(self):
        """
        刷新缓冲区（如果需要）
        """
        pass


class QtLogCapture:
    """
    简单的日志捕获器，可以用作Console的file参数
    将所有写入的内容通过信号发射
    """

    def __init__(self, signal):
        self.signal = signal
        self._buffer = ""

    def write(self, text: str) -> int:
        if not text:
            return 0

        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.rstrip()
            if line:
                self.signal.emit(line)
        return len(text)

    def flush(self) -> None:
        line = self._buffer.rstrip()
        if line:
            self.signal.emit(line)
        self._buffer = ""

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QTextEdit, QVBoxLayout
from qfluentwidgets import BodyLabel, CardWidget, ScrollArea


class TextLogCard(CardWidget):
    def __init__(self, title: str = "日志", parent=None):
        super().__init__(parent=parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 18, 18, 18)
        self.layout.setSpacing(12)

        self.title_label = BodyLabel(title, self)
        self.layout.addWidget(self.title_label)

        # 创建滚动区域
        self.scroll_area = ScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(self.title_label.sizeHint().height() * 10)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 创建只读文本编辑器作为滚动区域的内容
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("这里会显示执行日志")
        self.text_edit.setStyleSheet("background: transparent; border: none;")
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setFrameStyle(0)

        self.scroll_area.setWidget(self.text_edit)
        self.layout.addWidget(self.scroll_area)

    def append_log(self, message: str):
        if not message:
            return

        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        if self.text_edit.toPlainText():
            cursor.insertText("\n")
        cursor.insertText(message.rstrip())
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()

    def clear_log(self):
        self.text_edit.clear()

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout
from qfluentwidgets import BodyLabel, CardWidget


class TextLogCard(CardWidget):
    def __init__(self, title: str = "日志", parent=None):
        super().__init__(parent=parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 18, 18, 18)
        self.layout.setSpacing(12)

        self.title_label = BodyLabel(title, self)
        self.layout.addWidget(self.title_label)

        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("这里会显示执行日志")
        self.text_edit.setMinimumHeight(self.title_label.sizeHint().height() * 10)
        self.layout.addWidget(self.text_edit)

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

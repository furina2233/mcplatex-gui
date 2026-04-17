from PySide6.QtWidgets import QVBoxLayout
from qfluentwidgets import CardWidget, BodyLabel


class LogCard(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        self.title_label = BodyLabel(parent=self, text="日志")
        self.layout.addWidget(self.title_label)

        self.setFixedHeight(self.title_label.sizeHint().height() * 9)

        self.layout.addStretch(1)

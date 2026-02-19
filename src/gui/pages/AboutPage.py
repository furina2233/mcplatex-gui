from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import TitleLabel


class AboutPage(QWidget):
    """ 正文页面：关于界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # 给页面设置一个 ObjectName，方便路由管理
        self.setObjectName("aboutPage")

        self.layout = QVBoxLayout(self)
        self.label = TitleLabel("关于页面", self)

        # 居中显示
        self.layout.addWidget(self.label, 0, Qt.AlignCenter)

        # 设置页面背景（可选，透明背景会继承主窗口主题色）
        self.setStyleSheet("background: transparent;")
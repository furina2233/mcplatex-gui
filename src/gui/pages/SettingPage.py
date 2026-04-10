from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from qfluentwidgets import TitleLabel

from src.gui.utils.ScrollPageUtil import create_scrollable_page


class SettingPage(QWidget):
    """ 正文页面：设置界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # 给页面设置一个 ObjectName，方便路由管理
        self.setObjectName("settingPage")

        self.scrollArea, self.scrollWidget, self.layout = create_scrollable_page(self)
        self.label = TitleLabel("设置页面", self.scrollWidget)

        # 居中显示
        self.layout.addWidget(self.label, 0, Qt.AlignCenter)
        self.layout.addStretch(1)

        # 设置页面背景（可选，透明背景会继承主窗口主题色）
        self.setStyleSheet("background: transparent;")

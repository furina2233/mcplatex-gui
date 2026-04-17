from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from qfluentwidgets import CardWidget, PushButton, FluentIcon as FIF

from src.config.sys_config import VERSION
from src.gui.utils.ScrollPageUtil import create_scrollable_page


class AboutPage(QWidget):
    """ 正文页面：关于界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # 给页面设置一个 ObjectName，方便路由管理
        self.setObjectName("aboutPage")

        self.scrollArea, self.scrollWidget, self.layout = create_scrollable_page(self)
        self.layout.addSpacing(20)

        # 版本卡片
        version_card = self._create_version_card()
        self.layout.addWidget(version_card, 0, Qt.AlignCenter)

        self.layout.addSpacing(10)

        # 仓库地址卡片
        repo_card = self._create_repo_card()
        self.layout.addWidget(repo_card, 0, Qt.AlignCenter)

        self.layout.addStretch(1)

        # 设置页面背景（可选，透明背景会继承主窗口主题色）
        self.setStyleSheet("background: transparent;")

    def _create_version_card(self) -> CardWidget:
        """创建版本信息卡片"""
        card = CardWidget()
        card.setFixedWidth(400)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)

        left_label = QLabel("版本")
        left_label.setStyleSheet("font-size: 14px; font-weight: bold;")

        right_label = QLabel(f"v{VERSION}")
        right_label.setStyleSheet("font-size: 14px; color: #666666;")
        right_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(left_label)
        layout.addStretch()
        layout.addWidget(right_label)

        return card

    def _create_repo_card(self) -> CardWidget:
        """创建仓库地址卡片"""
        card = CardWidget()
        card.setFixedWidth(400)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)

        left_label = QLabel("仓库地址")
        left_label.setStyleSheet("font-size: 14px; font-weight: bold;")

        github_btn = PushButton("GitHub", icon=FIF.LINK)
        github_btn.clicked.connect(self._open_github)

        layout.addWidget(left_label)
        layout.addStretch()
        layout.addWidget(github_btn)

        return card

    def _open_github(self):
        """打开 GitHub 仓库链接"""
        QDesktopServices.openUrl("https://github.com/furina2233/mcplatex-gui")

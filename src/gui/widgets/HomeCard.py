import os
from typing import Union

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from qfluentwidgets import SettingCard, FluentIconBase, PushButton

from src.gui.utils.ExplorerUtil import open_in_explorer


class HomeCard(SettingCard):
    images_path = []
    images_path_changed = Signal(list)

    def __init__(self, parent=None, title="", icon: Union[str, QIcon, FluentIconBase] = None, content=""):
        super().__init__(parent=parent, title=title, icon=icon, content=content)

        icon_size = self.titleLabel.sizeHint().height() * 2
        self.iconLabel.setFixedSize(icon_size, icon_size)

        open_file_button = PushButton(parent=self, text="安装目录")
        open_file_button.clicked.connect(self._on_open_file_button_clicked)

        card_layout = self.hBoxLayout
        card_layout.setSpacing(10)
        card_layout.addWidget(open_file_button)
        card_layout.addSpacing(20)

    def _on_open_file_button_clicked(self):
        root_path = os.path.abspath(os.getcwd())
        open_in_explorer(self, root_path)

import os
from typing import Union

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, Qt
from PySide6.QtWidgets import QFileDialog
from qfluentwidgets import SettingCard, FluentIconBase, PushButton, InfoBarPosition, InfoBar, PrimaryPushButton

from src.gui.utils.ExplorerUtil import open_in_explorer
from src.gui.utils.MessageUtil import show_message, MessageType


class HomeCard(SettingCard):

    images_path = []
    images_path_changed = Signal(list)

    _transfer_finished = False

    def __init__(self,parent=None,title="",icon: Union[str, QIcon, FluentIconBase] = None,content = ""):
        super().__init__(parent=parent,title=title,icon=icon,content=content)

        icon_size = self.titleLabel.sizeHint().height() * 2
        self.iconLabel.setFixedSize(icon_size, icon_size)

        open_file_button = PushButton(parent=self, text="安装目录")
        open_file_button.clicked.connect(self._on_open_file_button_clicked)

        chose_image_button = PushButton(parent=self, text="选择图片")
        chose_image_button.clicked.connect(self._on_chose_image_button_clicked)

        click_to_transfer_button = PrimaryPushButton(parent=self, text="一键生成")
        click_to_transfer_button.clicked.connect(self._on_click_to_transfer_button_clicked)

        show_pdf_button = PushButton(parent=self, text="打开PDF")
        show_pdf_button.clicked.connect(self._on_show_pdf_button_clicked)

        card_layout = self.hBoxLayout
        card_layout.setSpacing(10)
        card_layout.addWidget(open_file_button)
        card_layout.addWidget(chose_image_button)
        card_layout.addWidget(click_to_transfer_button)
        card_layout.addWidget(show_pdf_button)
        card_layout.addSpacing(20)

    def _on_open_file_button_clicked(self):
        root_path = os.path.abspath(os.getcwd())
        open_in_explorer(self,root_path)

    def _on_chose_image_button_clicked(self):
        self.images_path = QFileDialog.getOpenFileNames(
            parent=self,
            caption="选择要转换的图片",
            dir="/",
            filter="图片文件 (*.png *.jpg *.jpeg);;所有文件 (*.*)"
        )[0]
        if self.images_path:
            show_message(self,"选择成功",MessageType.SUCCESS)
            self.images_path_changed.emit(self.images_path)

    def _on_click_to_transfer_button_clicked(self):
        if not self.images_path:
            show_message(self,"请先选择图片",MessageType.ERROR)
            return
        show_message(self,"转换成功",MessageType.SUCCESS)
        self._transfer_finished = True

    def _on_show_pdf_button_clicked(self):
        pdf_path = "latex_output/main.pdf"
        if self._transfer_finished and os.path.exists(pdf_path):
            open_in_explorer(self,pdf_path)
        else:
            show_message(self,"请先转换图片",MessageType.ERROR)

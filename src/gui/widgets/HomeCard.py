import asyncio
import os
from typing import Union

from PySide6.QtCore import Signal, QThread
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog
from qfluentwidgets import SettingCard, FluentIconBase, PushButton, PrimaryPushButton
from rich.console import Console

from services.work_service import WorkService
from src.gui.utils.ExplorerUtil import open_in_explorer
from src.gui.utils.MessageUtil import show_message, MessageType


class HomeCard(SettingCard):
    images_path = []
    images_path_changed = Signal(list)
    log_message = Signal(str)

    _transfer_finished = False

    def __init__(self, parent=None, title="", icon: Union[str, QIcon, FluentIconBase] = None, content=""):
        super().__init__(parent=parent, title=title, icon=icon, content=content)

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
        open_in_explorer(self, root_path)

    def _on_chose_image_button_clicked(self):
        self.images_path = QFileDialog.getOpenFileNames(
            parent=self,
            caption="选择要转换的图片",
            dir="../",
            filter="图片文件 (*.png *.jpg *.jpeg);;所有文件 (*.*)",
        )[0]
        if self.images_path:
            show_message(self, "选择成功", MessageType.SUCCESS)
            self.images_path_changed.emit(self.images_path)
            self.log_message.emit(f"已选择 {len(self.images_path)} 张图片")

    def _on_click_to_transfer_button_clicked(self):
        if not self.images_path:
            show_message(self, "请先选择图片", MessageType.ERROR)
            return

        sender = self.sender()
        sender.setEnabled(False)

        self.log_message.emit("=" * 30)
        self.log_message.emit("开始执行生成流程")

        self.work_thread = WorkThread(self.images_path)
        self.work_thread.log_message.connect(self.log_message.emit)
        self.work_thread.finished.connect(lambda success, msg: self._on_work_finished(success, msg, sender))
        self.work_thread.start()

    def _on_work_finished(self, success, error_msg, button):
        button.setEnabled(True)

        if success:
            self.log_message.emit("生成流程结束")
            show_message(self, "转换成功", MessageType.SUCCESS)
            self._transfer_finished = True
        else:
            if error_msg:
                self.log_message.emit(error_msg)
            show_message(self, "转换失败", MessageType.ERROR)
            print(error_msg)

    def _on_show_pdf_button_clicked(self):
        pdf_path = "latex_output/main.pdf"
        if self._transfer_finished and os.path.exists(pdf_path):
            open_in_explorer(self, pdf_path)
        else:
            show_message(self, "请先转换图片", MessageType.ERROR)


class WorkThread(QThread):
    finished = Signal(bool, str)
    log_message = Signal(str)

    def __init__(self, images_path):
        super().__init__()
        self.images_path = images_path

    def run(self):
        logger = _QtLogWriter(self.log_message)
        try:
            console = Console(file=logger, force_terminal=False, color_system=None, no_color=True, soft_wrap=True)
            service = WorkService(self.images_path, console=console)
            asyncio.run(service.quick_generate())
            logger.flush()
            self.finished.emit(True, "")
        except Exception as e:
            logger.flush()
            self.finished.emit(False, str(e))


class _QtLogWriter:
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

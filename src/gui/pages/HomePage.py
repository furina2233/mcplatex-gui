from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import FluentIcon as FIF

from src.gui.widgets.HomeCard import HomeCard
from src.gui.widgets.ImagesPreviewCard import ImagesPreviewCard
from src.gui.widgets.LogCard import LogCard

timer = QTimer()

class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homePage")
        self.images_path = []

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        self.home_card=self._add_home_card()
        self._add_images_preview_card()
        self._add_log_card()



        self._set_vector_layout()

    def _add_home_card(self):
        home_card = HomeCard(parent=self,title="McpLatex",icon="res/icons/icon_home_card.png",content="软件描述")
        self.layout.addWidget(home_card)
        return home_card

    def _add_images_preview_card(self):
        images_preview_card = ImagesPreviewCard(parent=self,home_card=self.home_card)
        self.layout.addWidget(images_preview_card)

    def _set_vector_layout(self):
        self.layout.addStretch(1)

    def _add_log_card(self):
        log_card = LogCard(parent=self)
        self.layout.addWidget(log_card)

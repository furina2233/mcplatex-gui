from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget

from src.gui.utils.ScrollPageUtil import create_scrollable_page
from src.gui.widgets.HomeCard import HomeCard
from src.gui.widgets.ImagesPreviewCard import ImagesPreviewCard
from src.gui.widgets.TextLogCard import TextLogCard

timer = QTimer()


class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homePage")
        self.images_path = []

        self.scrollArea, self.scrollWidget, self.layout = create_scrollable_page(self)

        self._add_log_card()
        self.home_card = self._add_home_card()
        self._add_images_preview_card()
        self._set_vector_layout()

    def _add_home_card(self):
        home_card = HomeCard(
            parent=self.scrollWidget,
            title="McpLatex",
            icon="../res/icons/icon_home_card.png",
            content="软件描述",
        )
        home_card.log_message.connect(self.log_card.append_log)
        self.layout.addWidget(home_card)
        return home_card

    def _add_images_preview_card(self):
        images_preview_card = ImagesPreviewCard(parent=self.scrollWidget, home_card=self.home_card)
        self.layout.addWidget(images_preview_card)

    def _set_vector_layout(self):
        self.layout.addStretch(1)

    def _add_log_card(self):
        self.log_card = TextLogCard(parent=self.scrollWidget)
        self.layout.addWidget(self.log_card)

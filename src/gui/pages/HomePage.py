from time import time

from PySide6.QtWidgets import QWidget

from src.gui.utils.ScrollPageUtil import create_scrollable_page
from src.gui.widgets.HomeCard import HomeCard


class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homePage")

        self.scrollArea, self.scrollWidget, self.layout = create_scrollable_page(self)

        self._add_home_card()
        self._set_vector_layout()

        self.setStyleSheet("background: transparent;")

    def _add_home_card(self):
        home_card = HomeCard(
            parent=self.scrollWidget,
            title="FreeWrite",
            icon="../res/icons/free_write.svg",
            content="让我们开始工作吧！",
        )
        self.layout.addWidget(home_card)
        return home_card

    def _set_vector_layout(self):
        self.layout.addStretch(1)

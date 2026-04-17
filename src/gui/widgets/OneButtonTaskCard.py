from typing import Union

from PySide6.QtGui import QIcon
from qfluentwidgets import FluentIcon as FIF, PushButton

from src.gui.widgets.TaskCard import TaskCard


class OneButtonTaskCard(TaskCard):
    def __init__(self, icon: Union[str, QIcon, FIF], title: str, content: str = None,
                 height_percent: float = 2.0, parent=None, button_text: str = '',
                 on_button_clicked=None):
        super().__init__(icon, title, content, height_percent, parent)
        self.card_button = PushButton(button_text, self.card)
        self.card_button.setMinimumWidth(self.card_button.width())
        if on_button_clicked:
            self.card_button.clicked.connect(on_button_clicked)
        self.card.addWidget(self.card_button)

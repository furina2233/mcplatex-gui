from enum import Enum

from PySide6.QtWidgets import QFrame
from qfluentwidgets import InfoBar, InfoBarPosition


class MessageType(Enum):
    SUCCESS = 0
    ERROR = 1

def show_message(parent: QFrame, text: str, message_type: MessageType):
    if message_type == MessageType.SUCCESS:
        InfoBar.success(
            title=text,
            content="",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=parent
        )
    elif message_type == MessageType.ERROR:
        InfoBar.error(
            title=text,
            content="",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=parent
        )

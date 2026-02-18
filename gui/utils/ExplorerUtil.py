import os
import platform
import subprocess

from PySide6.QtWidgets import QFrame

from gui.utils.MessageUtil import show_message, MessageType

def open_in_explorer(parent: QFrame, path: str):
    absolute_path = os.path.abspath(path)
    system_name = platform.system()
    try:
        if system_name == "Windows":
            os.startfile(absolute_path)
        elif system_name == "Darwin":
            subprocess.run(["open", absolute_path])
        else:
            subprocess.run(["xdg-open", absolute_path])
    except Exception as e:
        show_message(parent, "打开失败", MessageType.ERROR)

import sys

from PySide6.QtWidgets import QApplication
from dotenv import load_dotenv, find_dotenv

from src.gui.MainWindow import MainWindow

if __name__ == '__main__':
    load_dotenv("../.env")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

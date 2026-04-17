import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from dotenv import load_dotenv

from src.utils.model_config import ensure_model_env_file_exists

project_root = Path(__file__).resolve().parents[1]
ensure_model_env_file_exists()
load_dotenv(project_root / ".env", override=True)

from src.gui.MainWindow import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

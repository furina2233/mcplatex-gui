from PySide6.QtCore import Signal, QSize, Qt
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import ImageLabel, TransparentToolButton


class ImagePreviewLabel(ImageLabel):
    delete_button_clicked = Signal(str)
    image_double_clicked = Signal(str)
    
    def __init__(self,image_path:str, image_size: int, index: int, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setImage(self.image_path)
        self.setFixedSize(image_size,image_size)
        self.setScaledContents(False)
        self.setAlignment(Qt.AlignCenter)
        self.setBorderRadius(8, 8, 8, 8)

        self.index_label = QLabel(str(index), self)
        self.index_label.setFixedSize(24, 24)
        self.index_label.setAlignment(Qt.AlignCenter)
        self.index_label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(0, 0, 0, 80);
                        color: white;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 12px;
                    }
                """)
        self.index_label.move(0, 0)

        self.delete_button = TransparentToolButton(FIF.CLOSE, self)
        self.delete_button.setFixedSize(24, 24)
        self.delete_button.setIconSize(QSize(12, 12))
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.move(self.width() - self.delete_button.width(), 0)
        self.delete_button.clicked.connect(lambda: self.delete_button_clicked.emit(self.image_path))

        self.delete_button.setStyleSheet("""
            TransparentToolButton {
                background-color: rgba(0, 0, 0, 80);
                color: white;
                border-radius: 4px;
            }
            TransparentToolButton:hover {
                background-color: rgba(255, 0, 0, 150);
            }
        """)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.index_label.move(0, 0)
        self.delete_button.move(self.width() - self.delete_button.width(), 0)
    
    def mouseDoubleClickEvent(self, event):
        """双击图片时用系统默认程序打开"""
        if event.button() == Qt.LeftButton:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.image_path))
        super().mouseDoubleClickEvent(event)

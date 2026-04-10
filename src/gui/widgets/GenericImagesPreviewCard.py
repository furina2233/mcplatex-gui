from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, CardWidget, SingleDirectionScrollArea

from src.gui.widgets.ImagePreviewLabel import ImagePreviewLabel


class GenericImagesPreviewCard(CardWidget):
    image_removed = Signal(str)

    def __init__(self, title: str = "图片预览", parent=None):
        super().__init__(parent=parent)
        self._paths: list[str] = []

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 18, 18, 18)
        self.layout.setSpacing(12)

        self.title_label = BodyLabel(title, self)
        self.layout.addWidget(self.title_label)

        self.setFixedHeight(self.title_label.sizeHint().height() * 10)

        self.scroll_area = SingleDirectionScrollArea(self, orient=Qt.Horizontal)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(self.title_label.sizeHint().height() * 8)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_area.setViewportMargins(0, 0, 0, int(self.title_label.sizeHint().height() * 0.5))
        self.layout.addWidget(self.scroll_area)

        self.scroll_content = QWidget(self)
        self.images_layout = QHBoxLayout(self.scroll_content)
        self.images_layout.setContentsMargins(0, 5, 0, 5)
        self.images_layout.setSpacing(10)
        self.images_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.scroll_area.setWidget(self.scroll_content)

        self.empty_label = BodyLabel("暂未选择图片", self)
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.empty_label)

        self.layout.addStretch()
        self._refresh_images()

    def set_images(self, paths: list[str]):
        self._paths = list(paths)
        self._refresh_images()

    def _refresh_images(self):
        while self.images_layout.count():
            item = self.images_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.empty_label.setVisible(not self._paths)
        self.scroll_area.setVisible(bool(self._paths))

        if not self._paths:
            return

        image_size = self.title_label.sizeHint().height() * 6
        for index, path in enumerate(self._paths, start=1):
            image_item = ImagePreviewLabel(path, image_size, index, self)
            image_item.delete_button_clicked.connect(self.image_removed.emit)
            self.images_layout.addWidget(image_item)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import CardWidget, BodyLabel, SingleDirectionScrollArea

from gui.widgets.HomeCard import HomeCard
from gui.widgets.ImagePreviewLabel import ImagePreviewLabel


class ImagesPreviewCard(CardWidget):
    def __init__(self, home_card: HomeCard, parent=None):
        super().__init__(parent=parent)
        self.home_card = home_card

        self.layout = QVBoxLayout(self)

        self.title_label = BodyLabel(parent=self,text="图片预览")
        self.layout.addWidget(self.title_label)

        self.setFixedHeight(self.title_label.sizeHint().height()*10)

        self.scroll_area = SingleDirectionScrollArea(self, orient=Qt.Horizontal)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(self.title_label.sizeHint().height() * 8)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_area.setViewportMargins(0, 0, 0, int(self.title_label.sizeHint().height() * 0.5))

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.images_layout = QHBoxLayout(self.scroll_content)
        self.images_layout.setContentsMargins(0, 5, 0, 5)
        self.images_layout.setSpacing(10)
        self.images_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        self.layout.addStretch()
        self._add_on_images_selected_listener()

    def _add_on_images_selected_listener(self):
        self.home_card.images_path_changed.connect(self._refresh_images)

    def _refresh_images(self, paths: list):
        while self.images_layout.count():
            item = self.images_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        image_size = self.title_label.sizeHint().height() * 6

        for i,path in enumerate(paths,start=1):
            image_item = ImagePreviewLabel(path, image_size, i, self)
            image_item.delete_button_clicked.connect(lambda p=path: self._on_delete_button_clicked(p))
            self.images_layout.addWidget(image_item)

    def _on_delete_button_clicked(self, path):
        if path in self.home_card.images_path:
            self.home_card.images_path.remove(path)
            self.home_card.images_path_changed.emit(self.home_card.images_path)
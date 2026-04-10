from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget


def create_scrollable_page(page: QWidget, margins: tuple[int, int, int, int] = (30, 30, 30, 30), spacing: int = 20):
    outer_layout = QVBoxLayout(page)
    outer_layout.setContentsMargins(0, 0, 0, 0)

    scroll_area = QScrollArea(page)
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QScrollArea.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

    content_widget = QWidget(scroll_area)
    content_widget.setStyleSheet("background: transparent;")

    content_layout = QVBoxLayout(content_widget)
    content_layout.setContentsMargins(*margins)
    content_layout.setSpacing(spacing)

    scroll_area.setWidget(content_widget)
    outer_layout.addWidget(scroll_area)
    return scroll_area, content_widget, content_layout

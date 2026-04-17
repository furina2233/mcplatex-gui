from typing import Union

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QScrollArea,
                               QApplication)
from qfluentwidgets import FluentIcon as FIF, FluentStyleSheet
from qfluentwidgets.components.settings.expand_setting_card import HeaderSettingCard, ExpandBorderWidget, SpaceWidget


class TaskCard(QScrollArea):
    """ 自定义可展开设置卡片，用法参考ExpandSettingCard """

    def __init__(self, icon: Union[str, QIcon, FIF], title: str, content: str = None,
                 height_percent: float = 2.0, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('ExpandSettingCard')  # 伪装成ExpandSettingCard，否则无法获得Fluent风格的样式
        self.isExpand = False

        self.scrollWidget = QFrame(self)
        self.view = QFrame(self.scrollWidget)

        self.card = HeaderSettingCard(icon, title, content, self)

        self.header_height = int(self.card.sizeHint().height() * height_percent)
        self.card.setFixedHeight(self.header_height)

        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.viewLayout = QVBoxLayout(self.view)
        self.spaceWidget = SpaceWidget(self.scrollWidget)
        self.borderWidget = ExpandBorderWidget(self)

        self.expandAni = QPropertyAnimation(self.verticalScrollBar(), b'value', self)

        self.__initWidget()

    def __initWidget(self):
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        self.setFixedHeight(self.header_height)
        self.setViewportMargins(0, self.header_height, 0, 0)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setSpacing(0)
        self.scrollLayout.addWidget(self.view)
        self.scrollLayout.addWidget(self.spaceWidget)

        self.expandAni.setEasingCurve(QEasingCurve.OutQuad)
        self.expandAni.setDuration(200)

        self.view.setObjectName('view')
        self.scrollWidget.setObjectName('scrollWidget')
        self.setProperty('isExpand', False)

        FluentStyleSheet.EXPAND_SETTING_CARD.apply(self.card)
        FluentStyleSheet.EXPAND_SETTING_CARD.apply(self)

        self.card.installEventFilter(self)
        self.expandAni.valueChanged.connect(self._onExpandValueChanged)
        self.card.expandButton.clicked.connect(self.toggleExpand)

        self.setStyleSheet("""
            QScrollArea#ExpandSettingCard {
                background-color: transparent;
                border: none;
            }
            #scrollWidget, #view {
                background-color: transparent;
            }
        """)

    def addWidget(self, widget: QWidget):
        self.viewLayout.addWidget(widget)
        self._adjustViewSize()

    def setExpand(self, isExpand: bool):
        if self.isExpand == isExpand:
            return

        self._adjustViewSize()
        self.isExpand = isExpand
        self.setProperty('isExpand', isExpand)
        self.setStyle(QApplication.style())

        if isExpand:
            h = self.viewLayout.sizeHint().height()
            self.verticalScrollBar().setValue(h)
            self.expandAni.setStartValue(h)
            self.expandAni.setEndValue(0)
        else:
            self.expandAni.setStartValue(0)
            self.expandAni.setEndValue(self.verticalScrollBar().maximum())

        self.expandAni.start()
        self.card.expandButton.setExpand(isExpand)

    def toggleExpand(self):
        self.setExpand(not self.isExpand)

    def resizeEvent(self, e):
        self.card.resize(self.width(), self.header_height)
        self.scrollWidget.resize(self.width(), self.scrollWidget.height())

    def _onExpandValueChanged(self):
        vh = self.viewLayout.sizeHint().height()
        h = self.viewportMargins().top()  # 这里的 top 即 header_height
        # 总高度 = 头部高度 + (内容总高 - 当前滚动位置)
        self.setFixedHeight(max(h + vh - self.verticalScrollBar().value(), h))

    def _adjustViewSize(self):
        h = self.viewLayout.sizeHint().height()
        self.spaceWidget.setFixedHeight(h)
        if self.isExpand:
            self.setFixedHeight(self.header_height + h)

    def wheelEvent(self, e):
        e.ignore()

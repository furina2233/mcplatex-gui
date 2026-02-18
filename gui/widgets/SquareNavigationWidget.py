from PySide6.QtCore import Qt, QRect, QRectF, QPoint
from PySide6.QtGui import QPainter, QColor, QCursor
from qfluentwidgets import (NavigationWidget, isDarkTheme, drawIcon,
                            setFont)
from qfluentwidgets.common.color import autoFallbackThemeColor

class SquareNavigationWidget(NavigationWidget):
    def __init__(self, icon, text, parent=None):
        super().__init__(isSelectable=True, parent=parent)
        self._icon = icon
        self._text = text
        setFont(self)
        self.setFixedSize(68,68)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.TextAntialiasing |
                               QPainter.SmoothPixmapTransform)
        painter.setPen(Qt.NoPen)

        # 处理透明度（按下或禁用状态）
        if self.isPressed:
            painter.setOpacity(0.7)
        if not self.isEnabled():
            painter.setOpacity(0.4)

        # 绘制背景与指示器
        c = 255 if isDarkTheme() else 0
        globalRect = QRect(self.mapToGlobal(QPoint()), self.size())

        # 判定是否需要绘制选中背景
        if self.isSelected:
            # 绘制轻微的高亮背景
            painter.setBrush(QColor(c, c, c, 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

            # 绘制选中指示条（参考原版是在左侧，正方形建议放在左侧或底部）
            # 这里沿用原版左侧垂直小短条
            painter.setBrush(autoFallbackThemeColor(self.lightIndicatorColor, self.darkIndicatorColor))
            # 自定义指示器位置：左侧居中，高16，宽3
            painter.drawRoundedRect(QRectF(0, self.height() / 2 - 8, 3, 16), 1.5, 1.5)

        elif (self.isEnter and globalRect.contains(QCursor.pos())) and self.isEnabled():
            # 悬停背景
            painter.setBrush(QColor(c, c, c, 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

        # 预留顶部 12px 间距，图标大小 24x24
        icon_size = 24
        icon_rect = QRectF((self.width() - icon_size) / 2, 12, icon_size, icon_size)
        drawIcon(self._icon, painter, icon_rect)

        if self.isCompacted:
            return

        painter.setFont(self.font())
        painter.setPen(self.textColor())

        # 文字绘制在图标下方，留出 4px 间距
        text_rect = QRectF(0, icon_rect.bottom() + 4, self.width(), 20)
        painter.drawText(text_rect, Qt.AlignCenter, self._text)
    def icon(self):
        return self._icon
    def text(self):
        return self._text
    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.setFixedHeight(int(self.width()*0.9))  # 导航栏部件的高度为宽度的90%

from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget
from qfluentwidgets import PlainTextEdit, isDarkTheme


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.get_line_number_area_width(), 0)

    def paintEvent(self, event):
        if isDarkTheme():
            bg_color = QColor(32, 32, 32)
            text_color = QColor(120, 120, 120)
        else:
            bg_color = QColor(248, 248, 248)
            text_color = QColor(160, 160, 160)

        painter = QPainter(self)
        painter.fillRect(event.rect(), bg_color)

        self.editor._line_number_area_paint_event(event, text_color)

class LineNumberTextEdit(PlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)

        self._update_line_number_area_width(0)

    def get_line_number_area_width(self):
        """根据总行数的位数获取行号区域的宽度"""
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def _update_line_number_area_width(self, _):
        self.setViewportMargins(self.get_line_number_area_width() + 5, 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.get_line_number_area_width(), cr.height()))

    def _line_number_area_paint_event(self, event, text_color):
        """ 接收由 LineNumberArea 传来的颜色进行绘制 """
        painter = QPainter(self.line_number_area)
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(text_color)  # 使用动态颜色
                painter.drawText(0, int(top), self.line_number_area.width() - 5,
                                 self.fontMetrics().height(),
                                 Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1
# coding:utf-8
import sys

from PyQt5.QtCore import QEasingCurve, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from qfluentwidgets import FlowLayout, PushButton, PrimaryPushButton


class Demo(QWidget):

    def __init__(self):
        super().__init__()
        layout = FlowLayout(self, needAni=True)

        # customize animation
        layout.setAnimation(250, QEasingCurve.OutQuad)

        layout.setContentsMargins(30, 30, 30, 30)
        layout.setVerticalSpacing(20)
        layout.setHorizontalSpacing(10)

        layout.addWidget(PushButton('aiko'))
        layout.addWidget(PushButton('刘静爱'))
        layout.addWidget(PushButton('柳井爱子'))
        layout.addWidget(PushButton('aiko 赛高'))
        layout.addWidget(PushButton('aiko 太爱啦😘'))

        layout.insertWidget(1, PrimaryPushButton('西宫硝子'))

        self.resize(250, 300)
        self.setStyleSheet('Demo{background: white} QPushButton{padding: 5px 10px; font:15px "Microsoft YaHei"}')


if __name__ == '__main__':
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec_()

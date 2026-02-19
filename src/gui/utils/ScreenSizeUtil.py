from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication


def get_screen_size(percent: float) -> QSize:
    """
    获取屏幕尺寸的百分比大小
    :param percent: 百分比值（0.0 到 1.0 之间）
    :return: 屏幕尺寸的百分比大小
    """
    return QApplication.primaryScreen().availableGeometry().size() * percent
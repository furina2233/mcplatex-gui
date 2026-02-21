from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QApplication
from qfluentwidgets import FluentWindow, FluentIcon as FIF, NavigationItemPosition
from qfluentwidgets import Theme, setTheme

from src.gui.pages.AboutPage import AboutPage
from src.gui.pages.HomePage import HomePage
from src.gui.pages.PreviewPage import PreviewPage
from src.gui.pages.SettingPage import SettingPage
from src.gui.pages.ValuesPage import ValuesPage
from src.gui.utils.ScreenSizeUtil import get_screen_size
from src.gui.widgets.SquareNavigationWidget import SquareNavigationWidget

timer = QTimer()

# 防止导入被优化import删掉
PreviewPage,ValuesPage,AboutPage,SettingPage,HomePage

def _set_high_dpi_scaling():
    """
    开启高DPI缩放支持
    """
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        # _set_high_dpi_scaling()

        self.setWindowTitle("McpLatex")

        size = get_screen_size(0.55)
        size.setWidth(int(size.width()-(size.width()-size.height())/5))
        while float(size.width()) / float(size.height()) < 1.25:
            size.setWidth(int(size.width() * 1.25))
        self.setMinimumSize(size)
        self.resize(size)

        self._set_center_on_screen()
        setTheme(Theme.AUTO)
        timer.singleShot(1, lambda: self._set_navigation())

    def _set_center_on_screen(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        width = self.width()
        height = self.height()
        x = (screen_geometry.width() - width) // 2
        y = (screen_geometry.height() - height) // 2
        self.move(x, y)

    def _set_navigation(self):
        self.navigationInterface.addItemHeader("")
        self.navigationInterface.addItemHeader("")

        self._add_new_widget_to_navigation(FIF.HOME, "主页", "homePage")
        self._add_new_widget_to_navigation(FIF.CODE, "预览", "previewPage")
        self._add_new_widget_to_navigation(FIF.TAG, "变量", "valuesPage")
        self._add_new_widget_to_navigation(FIF.INFO, "关于", "aboutPage", NavigationItemPosition.BOTTOM)
        self._add_new_widget_to_navigation(FIF.SETTING, "设置", "settingPage", NavigationItemPosition.BOTTOM)

        self.navigationInterface.setIndicatorAnimationEnabled(False)
        self.navigationInterface.setExpandWidth(int(get_screen_size(0.05).width()))
        self.navigationInterface.setMenuButtonVisible(False)
        self.navigationInterface.setReturnButtonVisible(False)
        self.navigationInterface.expand(useAni=False)
        self.navigationInterface.setCurrentItem("homePage")
        self.navigationInterface.setMinimumWidth(int(get_screen_size(0.05).width()))
        self.navigationInterface.setCollapsible(False)

    def _add_new_widget_to_navigation(self, icon:FIF, text:str, route_key:str,
                                      position:NavigationItemPosition=NavigationItemPosition.TOP):
        widget = SquareNavigationWidget(icon=icon, text=text)
        class_name = route_key[0].upper() + route_key[1:]  # 把开头首字母转为大写，如 valuesPage 转为 ValuesPage
        if class_name in globals():
            page = globals()[class_name]
            page = page(self)
            page.setObjectName(route_key)
            self.stackedWidget.addWidget(page)
        self.navigationInterface.addWidget(
            routeKey=route_key,
            widget=widget,
            position=position,
            onClick=lambda : self._on_navigation_widget_button_clicked(route_key, page)
        )

    def _on_navigation_widget_button_clicked(self, route_key: str, widget: QWidget):
        self.stackedWidget.setCurrentWidget(widget)
        self.navigationInterface.setCurrentItem(route_key)
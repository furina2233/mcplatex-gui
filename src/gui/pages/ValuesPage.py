import os
from typing import Tuple, List

from PySide6.QtWidgets import QWidget, QHeaderView, QTableWidgetItem, QAbstractItemView, \
    QHBoxLayout
from dotenv import dotenv_values
from qfluentwidgets import setFont, TableWidget, BodyLabel, ComboBox

from src.gui.utils.ScrollPageUtil import create_scrollable_page


def _get_values_from_file(path: str) -> List[Tuple[str, str]]:
    """
    从指定路径的文件获取数据
    返回格式: [('变量1', '值1'), ('变量2', '值2'), ...]
    """
    if not os.path.exists(path):
        return []

    # 使用 dotenv_values 获取字典格式的数据
    env_dict = dotenv_values(path)

    # 将字典转换为元组列表，方便表格遍历
    # env_dict.items() 返回的是 (key, value) 对
    return list(env_dict.items())


class ValuesPage(QWidget):
    """ 正文页面：数值设置界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("valuesPage")

        self.scrollArea, self.scrollWidget, self.layout = create_scrollable_page(self)

        self._add_file_selection_box()
        self._add_values_table()
        self.layout.addStretch(1)

    def _add_values_table(self):
        """ 封装的表格创建方法 """
        self.tableView = TableWidget(self.scrollWidget)

        # 样式配置
        self.tableView.verticalHeader().hide()
        self.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableView.setSelectionMode(QAbstractItemView.NoSelection)
        self.tableView.setWordWrap(False)

        # 表头配置
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        v_header = self.tableView.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.Fixed)
        v_header.setDefaultSectionSize(40)

        setFont(self.tableView)
        self.layout.addWidget(self.tableView)

        self._refresh_table_data()

    def _add_file_selection_box(self):
        """ 封装的配置文件选择栏创建方法 """
        self.toolBarLayout = QHBoxLayout()
        self.toolBarLayout.setContentsMargins(0, 5, 0, 5)
        self.toolBarLayout.setSpacing(10)

        self.toolBarLayout.addStretch(1)

        self.configLabel = BodyLabel("配置文件", self.scrollWidget)
        self.comboBox = ComboBox(self.scrollWidget)
        self.comboBox.addItems(['.env'])
        self.comboBox.setCurrentIndex(0)
        self.comboBox.setMinimumWidth(200)
        self.comboBox.currentIndexChanged.connect(self._refresh_table_data)

        self.toolBarLayout.addWidget(self.configLabel)
        self.toolBarLayout.addWidget(self.comboBox)

        self.layout.addLayout(self.toolBarLayout)

        # 先禁用选择配置文件的下拉框
        self.configLabel.setVisible(False)
        self.comboBox.setVisible(False)

    def _refresh_table_data(self):
        """ 动态读取选中的文件并刷新表格内容 """
        file_name = self.comboBox.currentText()
        file_path = os.path.join(os.getcwd().split("\\src")[0], file_name)
        datas = _get_values_from_file(file_path)

        self.tableView.clearContents()
        self.tableView.setRowCount(max(len(datas), 10))
        self.tableView.setColumnCount(2)
        self.tableView.setHorizontalHeaderLabels(['变量', '值'])

        for i, (key, value) in enumerate(datas):
            self.tableView.setItem(i, 0, QTableWidgetItem(str(key)))
            self.tableView.setItem(i, 1, QTableWidgetItem(str(value)))

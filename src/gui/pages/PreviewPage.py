import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import BodyLabel, ComboBox, setFont

from src.gui.widgets.LineNumberTextEditWidget import LineNumberTextEdit


class PreviewPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("previewPage")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)

        self._add_file_selection_box()
        self._add_preview_file_editor()


    def _add_file_selection_box(self):
        self.toolBarLayout = QHBoxLayout()
        self.toolBarLayout.setContentsMargins(0, 5, 0, 5)
        self.toolBarLayout.setSpacing(10)

        self.toolBarLayout.addStretch(1)

        self.configLabel = BodyLabel("查看文件", self)
        self.comboBox = ComboBox(self)
        self.comboBox.addItems(['../result/main.tex','../result/template.cls','../result/main.log','../src/llm_request.log'])
        self.comboBox.setCurrentIndex(0)
        self.comboBox.setMinimumWidth(200)
        self.comboBox.currentIndexChanged.connect(self._refresh_table_data)

        self.toolBarLayout.addWidget(self.configLabel)
        self.toolBarLayout.addWidget(self.comboBox)

        self.layout.addLayout(self.toolBarLayout)

    def _add_preview_file_editor(self):
        self.textEdit = LineNumberTextEdit(self)
        self.textEdit.setReadOnly(True)
        self.textEdit.setFocusPolicy(Qt.NoFocus)
        self.textEdit.setPlaceholderText("")
        setFont(self.textEdit)
        self.layout.addWidget(self.textEdit)
        self._refresh_table_data()

    def _refresh_table_data(self):
        file_name = self.comboBox.currentText()
        file_path = os.path.join(os.getcwd(), file_name)

        content = ""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                content = "读取文件出错"
        else:
            content = "文件不存在"

        self.textEdit.setPlainText(content)
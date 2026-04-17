from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import PushButton, LineEdit, CardWidget, BodyLabel, ProgressBar, InfoBar, InfoBarPosition


class ManualAdjustmentCard(CardWidget):
    """手动调整卡片：用户输入反馈并执行单次迭代"""

    iterate_started = Signal(str)
    iterate_finished = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_adjusting = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = BodyLabel("手动调整", self)
        title.setObjectName("adjustmentTitle")
        layout.addWidget(title)

        self.feedback_edit = LineEdit(self)
        self.feedback_edit.setPlaceholderText("输入调整反馈，例如：标题字体偏小、页边距需要增大...")
        layout.addWidget(self.feedback_edit)

        button_layout = QHBoxLayout()
        self.start_button = PushButton("开始调整", self, icon=FIF.PLAY)
        self.start_button.clicked.connect(self._on_start_clicked)
        button_layout.addWidget(self.start_button)

        self.iterate_button = PushButton("执行迭代", self, icon=FIF.SYNC)
        self.iterate_button.clicked.connect(self._on_iterate_clicked)
        self.iterate_button.setEnabled(False)
        button_layout.addWidget(self.iterate_button)

        layout.addLayout(button_layout)

        self.progress_bar = ProgressBar(self)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def _on_start_clicked(self):
        """开始调整：初始化工作流"""
        self.start_button.setEnabled(False)
        self.iterate_button.setEnabled(True)
        self.feedback_edit.setEnabled(True)
        self._is_adjusting = True
        self.iterate_started.emit(self.feedback_edit.text())
        InfoBar.info(
            title="提示",
            content="已开始手动调整，请点击'执行迭代'进行迭代",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self,
        )

    def _on_iterate_clicked(self):
        """执行单次迭代"""
        feedback = self.feedback_edit.text()
        self.progress_bar.setVisible(True)
        self.iterate_button.setEnabled(False)
        self.iterate_started.emit(feedback)

    def on_iterate_finished(self, result: dict):
        """迭代完成回调"""
        self.progress_bar.setVisible(False)
        self.iterate_button.setEnabled(True)
        self._is_adjusting = True

        success = result.get("success", False)
        if success:
            InfoBar.success(
                title="成功",
                content=f"迭代 {result.get('attempt', 0)} 完成，已生成 PDF",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
        else:
            InfoBar.warning(
                title="提示",
                content="迭代完成，但未生成预览图",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )

        self.iterate_finished.emit(result)

    def reset(self):
        """重置卡片状态"""
        self.start_button.setEnabled(True)
        self.iterate_button.setEnabled(False)
        self.feedback_edit.setEnabled(True)
        self.feedback_edit.clear()
        self.progress_bar.setVisible(False)
        self._is_adjusting = False

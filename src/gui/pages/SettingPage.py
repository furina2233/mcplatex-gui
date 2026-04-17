import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from dotenv import dotenv_values, set_key
from qfluentwidgets import ExpandSettingCard, InfoBar, InfoBarPosition, LineEdit, SettingCard, \
    SpinBox

from src.gui.utils.ScrollPageUtil import create_scrollable_page
from src.llm_client import reload_model_clients
from src.utils.settings_manager import get_setting, set_setting


class IntSpinBoxSettingCard(SettingCard):
    """Integer spin box setting card."""

    def __init__(self, title, content, config_key, parent=None):
        self.config_key = config_key
        super().__init__(QIcon(), title, content, parent)
        self.spinBox = SpinBox(self)
        self.spinBox.setRange(1, 100)
        self.spinBox.setSingleStep(1)
        self.spinBox.setMinimumWidth(120)
        self.hBoxLayout.addWidget(self.spinBox)
        self.hBoxLayout.addSpacing(16)


class ModelExpandCard(ExpandSettingCard):
    """Expandable model config card."""

    def __init__(self, title, api_key_name, base_url_name, model_name, parent=None):
        super().__init__(QIcon(), title, "点击展开配置模型参数", parent)

        self.api_key_name = api_key_name
        self.base_url_name = base_url_name
        self.model_name = model_name
        self._has_unsaved_changes = False

        env_path = self._get_env_path()
        env_values = dotenv_values(env_path) if os.path.exists(env_path) else {}

        self.viewLayout.setSpacing(16)
        self.viewLayout.setContentsMargins(48, 16, 48, 16)

        api_key_layout = self._create_input_row("API Key", "模型服务的 API 密钥")
        self.api_key_edit = LineEdit()
        self.api_key_edit.setMinimumWidth(320)
        self.api_key_edit.setPlaceholderText(f"请输入 {api_key_name}（示例：abc）")
        self.api_key_edit.setText(env_values.get(api_key_name, "") or "")
        self.api_key_edit.editingFinished.connect(self._on_env_changed)
        api_key_layout.addWidget(self.api_key_edit)
        self.viewLayout.addLayout(api_key_layout)

        base_url_layout = self._create_input_row("Base URL", "模型服务的基础 URL")
        self.base_url_edit = LineEdit()
        self.base_url_edit.setMinimumWidth(320)
        self.base_url_edit.setPlaceholderText(f"请输入 {base_url_name}（示例：abc）")
        self.base_url_edit.setText(env_values.get(base_url_name, "") or "")
        self.base_url_edit.editingFinished.connect(self._on_env_changed)
        base_url_layout.addWidget(self.base_url_edit)
        self.viewLayout.addLayout(base_url_layout)

        model_name_layout = self._create_input_row("模型名称", "要使用的模型标识符")
        self.model_name_edit = LineEdit()
        self.model_name_edit.setMinimumWidth(320)
        self.model_name_edit.setPlaceholderText(f"请输入 {model_name}（示例：abc）")
        self.model_name_edit.setText(env_values.get(model_name, "") or "")
        self.model_name_edit.editingFinished.connect(self._on_env_changed)
        model_name_layout.addWidget(self.model_name_edit)
        self.viewLayout.addLayout(model_name_layout)

    def _get_env_path(self) -> str:
        return os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")

    def _create_input_row(self, title: str, content: str) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        content_label = QLabel(content)
        content_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(content_label)

        return layout

    def _on_env_changed(self):
        """Save env changes once editing is finished."""
        if self._has_unsaved_changes:
            return
        self._has_unsaved_changes = True

        self._save_env()
        InfoBar.warning(
            title="配置已保存",
            content="保存后，下一次执行任务时将使用新配置。",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=3000,
            parent=self.window(),
        )
        self._has_unsaved_changes = False

    def _save_env(self):
        env_path = self._get_env_path()
        set_key(env_path, self.api_key_name, self.api_key_edit.text())
        set_key(env_path, self.base_url_name, self.base_url_edit.text())
        set_key(env_path, self.model_name, self.model_name_edit.text())
        reload_model_clients()


class SettingPage(QWidget):
    """Settings page for application parameters."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("settingPage")

        self.scrollArea, self.scrollWidget, self.layout = create_scrollable_page(self)
        self._init_settings_cards()
        self.layout.addStretch(1)
        self.setStyleSheet("background: transparent;")

    def _init_settings_cards(self):
        self.max_retries_card = IntSpinBoxSettingCard(
            "最大重试次数",
            "自动流程中最大的重试次数。",
            "max_retries",
        )
        self.max_retries_card.spinBox.setRange(1, 20)
        self.max_retries_card.spinBox.setValue(get_setting("max_retries", 5))
        self.max_retries_card.spinBox.valueChanged.connect(self._on_max_retries_changed)
        self.layout.addWidget(self.max_retries_card)

        self.visual_model_card = ModelExpandCard(
            "视觉模型配置",
            "VISUAL_API_KEY",
            "VISUAL_BASE_URL",
            "VISUAL_MODEL",
        )
        self.layout.addWidget(self.visual_model_card)

        self.text_model_card = ModelExpandCard(
            "文本模型配置",
            "TEXT_API_KEY",
            "TEXT_BASE_URL",
            "TEXT_MODEL",
        )
        self.layout.addWidget(self.text_model_card)

    def _on_max_retries_changed(self, value: int):
        set_setting("max_retries", value)

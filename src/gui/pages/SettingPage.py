import os
from dotenv import dotenv_values, set_key

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SettingCard, SpinBox, ExpandSettingCard, InfoBar, InfoBarPosition, LineEdit

from src.gui.utils.ScrollPageUtil import create_scrollable_page
from src.utils.settings_manager import get_setting, set_setting


class IntSpinBoxSettingCard(SettingCard):
    """整数 SpinBox 设置卡片（无图标）"""

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
    """模型配置可展开卡片（无图标）"""

    def __init__(self, title, api_key_name, base_url_name, model_name, parent=None):
        super().__init__(QIcon(), title, "点击展开配置模型参数", parent)

        self.api_key_name = api_key_name
        self.base_url_name = base_url_name
        self.model_name = model_name
        self._has_unsaved_changes = False

        # 加载当前配置
        env_path = self._get_env_path()
        env_values = dotenv_values(env_path) if os.path.exists(env_path) else {}

        # 构建展开区域内容
        self.viewLayout.setSpacing(16)
        self.viewLayout.setContentsMargins(48, 16, 48, 16)

        # API Key 输入
        api_key_layout = self._create_input_row("API Key", "模型服务的 API 密钥")
        self.api_key_edit = LineEdit()
        self.api_key_edit.setMinimumWidth(320)
        self.api_key_edit.setPlaceholderText(f"请输入 {api_key_name}（默认：abc）")
        self.api_key_edit.setText(env_values.get(api_key_name, "abc"))
        self.api_key_edit.editingFinished.connect(self._on_env_changed)
        api_key_layout.addWidget(self.api_key_edit)
        self.viewLayout.addLayout(api_key_layout)

        # Base URL 输入
        base_url_layout = self._create_input_row("Base URL", "模型服务的基础 URL")
        self.base_url_edit = LineEdit()
        self.base_url_edit.setMinimumWidth(320)
        self.base_url_edit.setPlaceholderText(f"请输入 {base_url_name}（默认：abc）")
        self.base_url_edit.setText(env_values.get(base_url_name, "abc"))
        self.base_url_edit.editingFinished.connect(self._on_env_changed)
        base_url_layout.addWidget(self.base_url_edit)
        self.viewLayout.addLayout(base_url_layout)

        # Model Name 输入
        model_name_layout = self._create_input_row("模型名称", "要使用的模型标识符")
        self.model_name_edit = LineEdit()
        self.model_name_edit.setMinimumWidth(320)
        self.model_name_edit.setPlaceholderText(f"请输入 {model_name}（默认：abc）")
        self.model_name_edit.setText(env_values.get(model_name, "abc"))
        self.model_name_edit.editingFinished.connect(self._on_env_changed)
        model_name_layout.addWidget(self.model_name_edit)
        self.viewLayout.addLayout(model_name_layout)

    def _get_env_path(self) -> str:
        return os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")

    def _create_input_row(self, title: str, content: str) -> QVBoxLayout:
        """创建单行输入布局"""
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
        """任意输入框编辑完成时保存并提示需要重启"""
        if self._has_unsaved_changes:
            return
        self._has_unsaved_changes = True

        self._save_env()
        InfoBar.warning(
            title="需要重启",
            content="修改模型配置后需要重启应用才能生效",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=3000,
            parent=self.window(),
        )
        self._has_unsaved_changes = False

    def _save_env(self):
        """保存环境变量到 .env 文件"""
        env_path = self._get_env_path()
        set_key(env_path, self.api_key_name, self.api_key_edit.text())
        set_key(env_path, self.base_url_name, self.base_url_edit.text())
        set_key(env_path, self.model_name, self.model_name_edit.text())


class SettingPage(QWidget):
    """设置页面：允许用户调整迭代次数等参数"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("settingPage")

        self.scrollArea, self.scrollWidget, self.layout = create_scrollable_page(self)

        self._init_settings_cards()
        self.layout.addStretch(1)

        self.setStyleSheet("background: transparent;")

    def _init_settings_cards(self):
        # 迭代次数设置卡片
        self.max_retries_card = IntSpinBoxSettingCard(
            "最大迭代次数",
            "自动流程中最大尝试次数",
            "max_retries",
        )
        self.max_retries_card.spinBox.setRange(1, 20)
        self.max_retries_card.spinBox.setValue(get_setting("max_retries", 5))
        self.max_retries_card.spinBox.valueChanged.connect(self._on_max_retries_changed)
        self.layout.addWidget(self.max_retries_card)

        # 视觉模型配置
        self.visual_model_card = ModelExpandCard(
            "视觉模型配置",
            "VISUAL_API_KEY",
            "VISUAL_BASE_URL",
            "VISUAL_MODEL",
        )
        self.layout.addWidget(self.visual_model_card)

        # 文本模型配置
        self.text_model_card = ModelExpandCard(
            "文本模型配置",
            "TEXT_API_KEY",
            "TEXT_BASE_URL",
            "TEXT_MODEL",
        )
        self.layout.addWidget(self.text_model_card)

    def _on_max_retries_changed(self, value: int):
        """迭代次数变化时实时保存"""
        set_setting("max_retries", value)

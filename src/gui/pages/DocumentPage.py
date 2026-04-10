import asyncio
import os
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QWidget
from qfluentwidgets import BodyLabel, CardWidget, ComboBox, PrimaryPushButton, PushButton

from src.gui.utils.ScrollPageUtil import create_scrollable_page
from src.gui.utils.MessageUtil import MessageType, show_message
from src.gui.widgets.TextLogCard import TextLogCard
from src.latex_build_and_preview import build_and_preview
from src.services.workflow_support import list_template_files, normalize_tex_documentclass


class DocumentCompileThread(QThread):
    log_message = Signal(str)
    task_finished = Signal(bool, object)

    def __init__(self, template_path: str, document_path: str):
        super().__init__()
        self.template_path = template_path
        self.document_path = document_path

    def run(self):
        try:
            template_name = Path(self.template_path).stem
            cls_code = Path(self.template_path).read_text(encoding="utf-8")
            tex_code = Path(self.document_path).read_text(encoding="utf-8")
            tex_code = normalize_tex_documentclass(tex_code, template_name)

            pdf_generated, message, _, artifacts = asyncio.run(
                build_and_preview(cls_code, tex_code, job_name=template_name)
            )
            if message.strip():
                self.log_message.emit(message.strip())

            if not pdf_generated:
                self.task_finished.emit(False, {"message": "编译失败"})
                return

            self.log_message.emit("文档编译完成。")
            self.task_finished.emit(True, {"pdf_path": artifacts.get("pdf_path", "")})
        except Exception as exc:
            self.task_finished.emit(False, {"message": str(exc)})


class DocumentPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("documentPage")
        self.document_path = ""
        self._active_thread: QThread | None = None
        self.template_path_map: dict[str, str] = {}

        self.scrollArea, self.scrollWidget, self.layout = create_scrollable_page(self)

        self._add_toolbar_card()
        self._add_log_card()
        self.layout.addStretch(1)

        self._refresh_template_options()

    def _add_toolbar_card(self):
        self.toolbar_card = CardWidget(self.scrollWidget)
        layout = QHBoxLayout(self.toolbar_card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.select_document_button = PushButton("选择文档", self.toolbar_card)
        self.select_document_button.clicked.connect(self._on_select_document_clicked)

        self.template_combo = ComboBox(self.toolbar_card)
        self.template_combo.setMinimumWidth(220)

        self.compile_button = PrimaryPushButton("编译", self.toolbar_card)
        self.compile_button.clicked.connect(self._on_compile_clicked)

        self.document_label = BodyLabel("未选择文档", self.toolbar_card)

        layout.addWidget(self.select_document_button)
        layout.addWidget(self.template_combo)
        layout.addWidget(self.compile_button)
        layout.addStretch(1)
        layout.addWidget(self.document_label)

        self.layout.addWidget(self.toolbar_card)

    def _add_log_card(self):
        self.log_card = TextLogCard(parent=self.scrollWidget)
        self.layout.addWidget(self.log_card)

    def _on_select_document_clicked(self):
        document_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择要编译的文档",
            "../",
            "LaTeX 文档 (*.tex);;所有文件 (*.*)",
        )
        if not document_path:
            return

        self.document_path = document_path
        self.document_label.setText(os.path.basename(document_path))
        self.log_card.append_log(f"已选择文档：{document_path}")
        show_message(self, "选择成功", MessageType.SUCCESS)

    def _on_compile_clicked(self):
        self._refresh_template_options()
        template_name = self.template_combo.currentText().strip()
        template_path = self.template_path_map.get(template_name, "")
        if not self.document_path:
            show_message(self, "请先选择文档", MessageType.ERROR)
            return
        if not template_path:
            show_message(self, "未找到可用模板", MessageType.ERROR)
            return

        self.log_card.append_log("=" * 30)
        self.log_card.append_log(
            f"开始编译文档，模板：{template_name}.cls，文档：{os.path.basename(self.document_path)}"
        )
        self._set_busy(True)

        self._active_thread = DocumentCompileThread(template_path, self.document_path)
        self._active_thread.log_message.connect(self.log_card.append_log)
        self._active_thread.task_finished.connect(self._on_compile_finished)
        self._active_thread.start()

    def _on_compile_finished(self, success: bool, payload: object):
        self._set_busy(False)
        if success:
            show_message(self, "编译成功", MessageType.SUCCESS)
        else:
            message = payload.get("message", "编译失败") if isinstance(payload, dict) else str(payload)
            self.log_card.append_log(message)
            show_message(self, "编译失败", MessageType.ERROR)

    def _refresh_template_options(self):
        current_text = self.template_combo.currentText()
        templates = list_template_files()

        self.template_combo.clear()
        self.template_path_map = {}
        for template_path in templates:
            self.template_path_map[template_path.stem] = str(template_path)
            self.template_combo.addItem(template_path.stem)

        if current_text:
            index = self.template_combo.findText(current_text)
            if index >= 0:
                self.template_combo.setCurrentIndex(index)

    def _set_busy(self, is_busy: bool):
        self.select_document_button.setEnabled(not is_busy)
        self.template_combo.setEnabled(not is_busy)
        self.compile_button.setEnabled(not is_busy)

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_template_options()

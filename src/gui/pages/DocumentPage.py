import asyncio
import os
import shutil
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QWidget, QVBoxLayout
from qfluentwidgets import BodyLabel, CardWidget, ComboBox, PrimaryPushButton, PushButton, LineEdit, FluentIcon as FIF

from src.gui.utils.ExplorerUtil import open_in_explorer
from src.gui.utils.ScrollPageUtil import create_scrollable_page
from src.gui.utils.MessageUtil import MessageType, show_message
from src.gui.widgets.TextLogCard import TextLogCard
from src.latex_build_and_preview import build_and_preview
from src.services.workflow_support import (
    cls_dir,
    tex_dir,
    create_work_name,
    list_template_files,
    list_tex_files,
    load_cls_output,
    load_work_item_sources,
    normalize_cls_output,
    normalize_tex_documentclass,
    save_final_results,
    save_work_item,
)
from src.services.work_service import WorkService
from src.utils.cls_builder import build_cls_code
from src.utils.qt_log_bridge import QtConsoleBridge


class DocumentCompileThread(QThread):
    log_message = Signal(str)
    task_finished = Signal(bool, object)

    def __init__(self, template_path: str, document_path: str):
        super().__init__()
        self.template_path = template_path
        self.document_path = document_path

    def run(self):
        try:
            # 创建Qt日志桥接器，将console输出转发到log_message信号
            qt_console = QtConsoleBridge()
            qt_console.log_message.connect(self.log_message.emit)

            template_name = Path(self.template_path).stem
            cls_code = Path(self.template_path).read_text(encoding="utf-8")
            tex_code = Path(self.document_path).read_text(encoding="utf-8")
            tex_code = normalize_tex_documentclass(tex_code, template_name)

            pdf_generated, message, _, artifacts = asyncio.run(
                build_and_preview(cls_code, tex_code, job_name=template_name, console=qt_console)
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


class DocumentManualAdjustThread(QThread):
    """文档区手动调整线程"""
    log_message = Signal(str)
    task_finished = Signal(bool, object)

    def __init__(self, work_service: WorkService, user_feedback: str = ""):
        super().__init__()
        self.work_service = work_service
        self.user_feedback = user_feedback

    def run(self):
        try:
            self.log_message.emit(f"本次执行的任务：手动调整模板")
            # 无论是否有反馈，都需要先初始化手动调整流程
            asyncio.run(self.work_service.start_manual_adjustment())
            # 然后执行用户反馈的迭代
            result = asyncio.run(self.work_service.manual_iterate(self.user_feedback))
            self.log_message.emit("任务已完成")
            self.task_finished.emit(True, result)
        except Exception as exc:
            self.task_finished.emit(False, {"message": str(exc)})


class DocumentPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("documentPage")
        self.document_path = ""
        self._active_thread: QThread | None = None
        self.current_pdf_path = ""
        self.template_path_map: dict[str, str] = {}
        self.tex_path_map: dict[str, str] = {}
        self.images_path: list[str] = []

        self.scrollArea, self.scrollWidget, self.layout = create_scrollable_page(self)

        self._add_toolbar_card()
        self._add_document_card()
        self._add_template_card()
        self._add_log_card()
        self._add_manual_adjust_card()
        self.layout.addStretch(1)

        self._refresh_template_options()
        self._refresh_tex_options()

        self.setStyleSheet("background: transparent;")

    def _add_toolbar_card(self):
        """工具栏：导入文档、编译、打开PDF"""
        self.toolbar_card = CardWidget(self.scrollWidget)
        layout = QHBoxLayout(self.toolbar_card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.import_document_button = PushButton("导入", self.toolbar_card)
        self.import_document_button.clicked.connect(self._on_import_document_clicked)

        self.compile_button = PrimaryPushButton("编译", self.toolbar_card)
        self.compile_button.clicked.connect(self._on_compile_clicked)

        self.open_pdf_button = PushButton("打开PDF", self.toolbar_card)
        self.open_pdf_button.clicked.connect(self._on_open_pdf_clicked)

        self.document_label = BodyLabel("未选择文档", self.toolbar_card)

        layout.addWidget(self.import_document_button)
        layout.addWidget(self.compile_button)
        layout.addWidget(self.open_pdf_button)
        layout.addStretch(1)
        layout.addWidget(self.document_label)

        self.layout.addWidget(self.toolbar_card)

    def _add_document_card(self):
        """文档选择卡片"""
        self.document_card = CardWidget(self.scrollWidget)
        layout = QHBoxLayout(self.document_card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        document_label = BodyLabel("选择文档：", self.document_card)
        self.document_combo = ComboBox(self.document_card)
        self.document_combo.setMinimumWidth(220)

        layout.addWidget(document_label)
        layout.addWidget(self.document_combo)
        layout.addStretch(1)

        self.layout.addWidget(self.document_card)

    def _add_template_card(self):
        """模板选择卡片"""
        self.template_card = CardWidget(self.scrollWidget)
        layout = QHBoxLayout(self.template_card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        template_label = BodyLabel("选择模板：", self.template_card)
        self.template_combo = ComboBox(self.template_card)
        self.template_combo.setMinimumWidth(220)

        layout.addWidget(template_label)
        layout.addWidget(self.template_combo)
        layout.addStretch(1)

        self.layout.addWidget(self.template_card)

    def _add_log_card(self):
        self.log_card = TextLogCard(parent=self.scrollWidget)
        self.layout.addWidget(self.log_card)

    def _add_manual_adjust_card(self):
        """添加手动调整卡片"""
        self.manual_adjust_card = CardWidget(self.scrollWidget)
        layout = QVBoxLayout(self.manual_adjust_card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # 标题
        title_label = BodyLabel("手动调整", self.manual_adjust_card)
        layout.addWidget(title_label)

        # 反馈输入区
        feedback_layout = QHBoxLayout()
        self.feedback_input = LineEdit(self.manual_adjust_card)
        self.feedback_input.setPlaceholderText("输入调整反馈，例如：标题字体偏小、页边距需要增大...")
        feedback_layout.addWidget(self.feedback_input)

        self.start_adjust_button = PushButton("开始调整", self.manual_adjust_card, icon=FIF.PLAY)
        self.start_adjust_button.clicked.connect(self._on_manual_adjust_start_clicked)

        feedback_layout.addWidget(self.start_adjust_button)
        layout.addLayout(feedback_layout)

        self.layout.addWidget(self.manual_adjust_card)

    def _on_import_document_clicked(self):
        """导入文档：复制文件到work/tex/"""
        document_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择要导入的文档",
            "../",
            "LaTeX 文档 (*.tex);;所有文件 (*.*)",
        )
        if not document_path:
            return

        # 复制到 work/tex/
        file_name = Path(document_path).name
        dest_path = tex_dir() / file_name
        
        # 如果文件已存在，添加时间戳避免冲突
        if dest_path.exists():
            timestamp = create_work_name()
            base_name = Path(file_name).stem
            ext = Path(file_name).suffix
            new_name = f"{base_name}_{timestamp}{ext}"
            dest_path = tex_dir() / new_name

        shutil.copy2(document_path, dest_path)

        self.document_path = str(dest_path)
        self.document_label.setText(dest_path.name)
        self.log_card.append_log(f"已导入文档：{dest_path.name}")
        self._refresh_tex_options()
        show_message(self, "导入成功", MessageType.SUCCESS)

    def _on_select_document_clicked(self):
        """选择已导入的文档"""
        doc_name = self.document_combo.currentText().strip()
        if doc_name and doc_name in self.tex_path_map:
            self.document_path = self.tex_path_map[doc_name]
            self.document_label.setText(doc_name)
            self.log_card.append_log(f"已选择文档：{doc_name}")

    def _on_compile_clicked(self):
        self._refresh_template_options()
        self._refresh_tex_options()
        
        template_name = self.template_combo.currentText().strip()
        template_path = self.template_path_map.get(template_name, "")
        
        doc_name = self.document_combo.currentText().strip()
        document_path = self.tex_path_map.get(doc_name, self.document_path)
        
        if not document_path:
            show_message(self, "请先导入或选择文档", MessageType.ERROR)
            return
        if not template_path:
            show_message(self, "未找到可用模板", MessageType.ERROR)
            return

        self.log_card.append_log("=" * 30)
        self.log_card.append_log(
            f"开始编译文档，模板：{template_name}.cls，文档：{Path(document_path).name}"
        )
        self._set_busy(True)

        self._active_thread = DocumentCompileThread(template_path, document_path)
        self._active_thread.log_message.connect(self.log_card.append_log)
        self._active_thread.task_finished.connect(self._on_compile_finished)
        self._active_thread.start()

    def _on_compile_finished(self, success: bool, payload: object):
        self._active_thread = None
        self._set_busy(False)
        if success:
            result = payload if isinstance(payload, dict) else {}
            self.current_pdf_path = result.get("pdf_path", "") or ""
            if self.current_pdf_path:
                self.log_card.append_log(f"已生成PDF：{Path(self.current_pdf_path).name}")
            show_message(self, "编译成功", MessageType.SUCCESS)
        else:
            message = payload.get("message", "编译失败") if isinstance(payload, dict) else str(payload)
            self.log_card.append_log(message)
            show_message(self, "编译失败", MessageType.ERROR)

    def _on_open_pdf_clicked(self):
        if not self.current_pdf_path or not Path(self.current_pdf_path).exists():
            show_message(self, "当前没有可打开的 PDF", MessageType.ERROR)
            return
        open_in_explorer(self, self.current_pdf_path)

    def _on_manual_adjust_start_clicked(self):
        """开始手动调整流程"""
        template_name = self.template_combo.currentText().strip()
        if not template_name:
            show_message(self, "请先选择模板", MessageType.ERROR)
            return

        feedback = self.feedback_input.text().strip()
        self.start_adjust_button.setEnabled(False)
        self.feedback_input.setEnabled(False)
        self._set_busy(True)

        qt_console = QtConsoleBridge()
        qt_console.log_message.connect(self.log_card.append_log)
        self._manual_adjust_service = WorkService(self.images_path, console=qt_console)

        self._active_thread = DocumentManualAdjustThread(self._manual_adjust_service, feedback)
        self._active_thread.log_message.connect(self.log_card.append_log)
        self._active_thread.task_finished.connect(self._on_manual_adjust_finished)
        self._active_thread.start()

    def _on_manual_adjust_finished(self, success: bool, payload: object):
        self._active_thread = None
        self._set_busy(False)
        if success:
            result = payload if isinstance(payload, dict) else {}
            work_name = result.get("work_name", "")
            if work_name:
                self._refresh_template_options(work_name)
            self.current_pdf_path = result.get("pdf_path", "") or ""
            if self.current_pdf_path:
                self.log_card.append_log(f"已生成PDF：{Path(self.current_pdf_path).name}")
            show_message(self, "手动调整完成", MessageType.SUCCESS)
        else:
            message = payload.get("message", "调整失败") if isinstance(payload, dict) else str(payload)
            self.log_card.append_log(message)
            show_message(self, "手动调整失败", MessageType.ERROR)

        self.start_adjust_button.setEnabled(True)
        self.feedback_input.setEnabled(True)

    def _refresh_template_options(self, selected_name: str = ""):
        previous_name = selected_name or self.template_combo.currentText()
        templates = list_template_files()

        self.template_combo.clear()
        self.template_path_map = {}
        for template_path in templates:
            self.template_path_map[template_path.stem] = str(template_path)
            self.template_combo.addItem(template_path.stem)

        if previous_name:
            index = self.template_combo.findText(previous_name)
            if index >= 0:
                self.template_combo.setCurrentIndex(index)

    def _refresh_tex_options(self, selected_name: str = ""):
        """刷新文档下拉菜单选项"""
        previous_name = selected_name or self.document_combo.currentText()
        tex_files = list_tex_files()

        self.document_combo.clear()
        self.tex_path_map = {}
        for tex_path in tex_files:
            self.tex_path_map[tex_path.stem] = str(tex_path)
            self.document_combo.addItem(tex_path.stem)

        if previous_name:
            index = self.document_combo.findText(previous_name)
            if index >= 0:
                self.document_combo.setCurrentIndex(index)
    
    def on_template_generated(self, work_name: str):
        """
        槽函数:当模板区生成新模板和tex后被调用
        刷新文档列表并选中最新的文档
        """
        # 刷新文档列表
        self._refresh_tex_options(work_name)
        self.log_card.append_log(f"已自动选中文档：{work_name}.tex")

    def _set_busy(self, is_busy: bool):
        self.import_document_button.setEnabled(not is_busy)
        self.template_combo.setEnabled(not is_busy)
        self.document_combo.setEnabled(not is_busy)
        self.compile_button.setEnabled(not is_busy)
        self.open_pdf_button.setEnabled(not is_busy)
        self.feedback_input.setEnabled(not is_busy)
        self.start_adjust_button.setEnabled(not is_busy)

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_template_options()
        self._refresh_tex_options()

import asyncio
import shutil
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QWidget, QVBoxLayout
from qfluentwidgets import BodyLabel, CardWidget, ComboBox, PrimaryPushButton, PushButton, LineEdit
from qfluentwidgets import FluentIcon as FIF

from src.gui.utils.ExplorerUtil import open_in_explorer
from src.gui.utils.MessageUtil import MessageType, show_message
from src.gui.utils.ScrollPageUtil import create_scrollable_page
from src.gui.widgets.GenericImagesPreviewCard import GenericImagesPreviewCard
from src.gui.widgets.TextLogCard import TextLogCard
from src.services.work_service import WorkService
from src.services.workflow_support import (
    cls_dir,
    create_work_name,
    list_template_files,
    load_cls_output,
    load_work_item_sources,
    normalize_cls_output,
    normalize_tex_documentclass,
    save_final_results,
    save_work_item,
)
from src.utils.cls_builder import build_cls_code
from src.utils.error_util import get_user_facing_error_message
from src.utils.qt_log_bridge import QtConsoleBridge
from src.utils.settings_manager import get_setting


class TemplateWorkflowThread(QThread):
    log_message = Signal(str)
    task_finished = Signal(bool, object)

    def __init__(self, image_paths: list[str], mode: str, selected_template_name: str = ""):
        super().__init__()
        self.image_paths = list(image_paths)
        self.mode = mode
        self.selected_template_name = selected_template_name

    def run(self):
        try:
            result = asyncio.run(self._run_async())
            self.task_finished.emit(True, result)
        except Exception as exc:
            self.task_finished.emit(
                False,
                {"message": str(exc), "exception_type": exc.__class__.__name__},
            )

    async def _run_async(self):
        # 创建Qt日志桥接器，将console输出转发到log_message信号
        qt_console = QtConsoleBridge()
        qt_console.log_message.connect(self.log_message.emit)

        service = WorkService(self.image_paths, console=qt_console)
        if self.mode in {"extract_validate", "extract_only"}:
            return await self._run_extract(service)
        return await self._run_optimize(service)

    async def _run_extract(self, service: WorkService):
        if self.mode == "extract_only":
            work_name = create_work_name()
            self.log_message.emit(f"本次执行的任务：提取模式生成模板 {work_name}")

            style_report, cls_output, tex_output = await service.generate_tex_and_cls(self.image_paths)
            self.log_message.emit("已生成 tex 文件")
            self.log_message.emit("已生成 cls 文件")
            cls_output = normalize_cls_output(cls_output, class_name=work_name)
            cls_code = build_cls_code(cls_output)
            tex_code = normalize_tex_documentclass(tex_output.tex_code, work_name)

            save_final_results(
                work_name,
                cls_output,
                tex_output,
                cls_code,
                tex_code,
                [],
                style_report=style_report,
                source_images=self.image_paths,
            )
            self.log_message.emit("任务已完成")
            return {"work_name": work_name, "pdf_path": "", "created": True}

        max_retries = get_setting("max_retries", 5)
        self.log_message.emit(f"本次执行的任务：一键提取并验证，最多进行 {max_retries} 轮视觉优化。")
        service.max_retries = max_retries
        result = await service.quick_generate(self.image_paths)
        self.log_message.emit("任务已完成")
        return {
            "work_name": result["work_name"],
            "pdf_path": result.get("pdf_path", ""),
            "created": True,
        }

    async def _run_optimize(self, service: WorkService):
        if not self.selected_template_name:
            raise RuntimeError("请先选择要优化的模板。")

        cls_output = load_cls_output(self.selected_template_name)
        if cls_output is None:
            raise RuntimeError("无法从选中的 cls 文件恢复模板配置对象。")

        cls_code, tex_code = load_work_item_sources(self.selected_template_name)
        if not cls_code or not tex_code:
            raise RuntimeError("当前模板缺少对应的源文件。")

        self.log_message.emit(f"本次执行的任务：优化模板 {self.selected_template_name}.cls")
        compile_result = await service.compile_files(cls_code, tex_code, job_name=self.selected_template_name)
        if not compile_result.pdf_generated or not compile_result.images:
            raise RuntimeError("优化前编译验证失败，无法继续优化。")
        self.log_message.emit("编译成功")

        max_retries = get_setting("max_retries", 5)
        style_report = await asyncio.to_thread(service.generation_service.analyze_style, self.image_paths)
        current_cls = cls_output
        current_cls_code = cls_code
        current_pdf_path = compile_result.pdf_path
        current_images = compile_result.images

        for attempt in range(1, max_retries + 1):
            self.log_message.emit(f"迭代循环 ({attempt}/{max_retries})")
            revised_cls, audit_result = await service.optimize_after_compile(
                style_report,
                current_cls,
                self.image_paths[0],
                current_images[0],
            )
            if audit_result.passed:
                self.log_message.emit("任务已完成")
                return {
                    "work_name": self.selected_template_name,
                    "pdf_path": current_pdf_path,
                    "created": False,
                }

            new_work_name = create_work_name()
            revised_cls = normalize_cls_output(revised_cls, class_name=new_work_name)
            revised_cls_code = build_cls_code(revised_cls)
            revised_tex_code = normalize_tex_documentclass(tex_code, new_work_name)

            self.log_message.emit("已生成 tex 文件")
            self.log_message.emit("已生成 cls 文件")
            save_work_item(
                new_work_name,
                revised_cls_code,
                revised_tex_code,
                cls_output=revised_cls,
                style_report=style_report,
                source_images=self.image_paths,
            )

            revised_compile_result = await service.compile_files(revised_cls_code, revised_tex_code,
                                                                 job_name=new_work_name)
            if not revised_compile_result.pdf_generated or not revised_compile_result.images:
                raise RuntimeError("优化后的模板编译失败。")
            self.log_message.emit("编译成功")

            current_cls = revised_cls
            current_cls_code = revised_cls_code
            current_pdf_path = revised_compile_result.pdf_path
            current_images = revised_compile_result.images
            self.log_message.emit(f"已生成优化模板：{new_work_name}.cls")

            current_tex = normalize_tex_documentclass(tex_code, new_work_name)
            tex_code = current_tex
            self.selected_template_name = new_work_name

        self.log_message.emit("任务已完成")
        return {
            "work_name": self.selected_template_name,
            "pdf_path": current_pdf_path,
            "created": True,
        }


class TemplateCompileThread(QThread):
    log_message = Signal(str)
    task_finished = Signal(bool, object)

    def __init__(self, work_name: str):
        super().__init__()
        self.work_name = work_name

    def run(self):
        try:
            result = asyncio.run(self._run_async())
            self.task_finished.emit(True, result)
        except Exception as exc:
            self.task_finished.emit(
                False,
                {"message": str(exc), "exception_type": exc.__class__.__name__},
            )

    async def _run_async(self):
        # 创建Qt日志桥接器，将console输出转发到log_message信号
        qt_console = QtConsoleBridge()
        qt_console.log_message.connect(self.log_message.emit)

        cls_code, tex_code = load_work_item_sources(self.work_name)
        if not cls_code or not tex_code:
            raise RuntimeError("当前模板缺少对应的源文件。")

        service = WorkService([], console=qt_console)
        compile_result = await service.compile_files(cls_code, tex_code, job_name=self.work_name)
        if not compile_result.pdf_generated:
            raise RuntimeError("编译失败")

        self.log_message.emit("编译成功")
        self.log_message.emit("任务已完成")
        return {"work_name": self.work_name, "pdf_path": compile_result.pdf_path}


class ManualAdjustThread(QThread):
    """手动调整线程"""
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
            self.task_finished.emit(
                False,
                {"message": str(exc), "exception_type": exc.__class__.__name__},
            )


class TemplatePage(QWidget):
    # 信号:当新模板和tex生成后发出
    template_generated = Signal(str)  # 参数为新生成的work_name

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("templatePage")
        self.images_path: list[str] = []
        self._active_thread: QThread | None = None
        self.current_pdf_path = ""
        self.template_path_map: dict[str, str] = {}

        self.scrollArea, self.scrollWidget, self.layout = create_scrollable_page(self)

        self._add_start_card()
        self._add_template_card()
        self._add_preview_card()
        self._add_log_card()
        self._add_manual_adjust_card()
        self.layout.addStretch(1)
        self._refresh_template_options()

        self.setStyleSheet("background: transparent;")

    def _add_start_card(self):
        self.start_card = CardWidget(self.scrollWidget)
        layout = QHBoxLayout(self.start_card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.select_image_button = PushButton("选择图片", self.start_card, icon=FIF.PHOTO)
        self.select_image_button.clicked.connect(self._on_select_image_clicked)

        self.mode_combo = ComboBox(self.start_card)
        self.mode_combo.addItems(["一键提取并验证", "仅提取", "优化改进"])
        self.mode_combo.setMinimumWidth(180)

        self.start_button = PrimaryPushButton("开始", self.start_card)
        self.start_button.clicked.connect(self._on_start_clicked)

        self.stop_button = PushButton("停止", self.start_card)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._on_stop_clicked)

        layout.addWidget(self.select_image_button)
        layout.addWidget(self.mode_combo)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addStretch(1)
        self.layout.addWidget(self.start_card)

    def _add_template_card(self):
        self.template_card = CardWidget(self.scrollWidget)
        layout = QHBoxLayout(self.template_card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.import_template_button = PushButton("导入", self.template_card)
        self.import_template_button.clicked.connect(self._on_import_template_clicked)

        template_label = BodyLabel("选择模板：", self.template_card)
        self.template_combo = ComboBox(self.template_card)
        self.template_combo.setMinimumWidth(240)

        self.compile_button = PushButton("编译验证", self.template_card)
        self.compile_button.clicked.connect(self._on_compile_clicked)

        self.open_template_button = PushButton("打开模板", self.template_card)
        self.open_template_button.clicked.connect(self._on_open_template_clicked)

        self.open_pdf_button = PushButton("打开PDF", self.template_card)
        self.open_pdf_button.clicked.connect(self._on_open_pdf_clicked)

        layout.addWidget(self.import_template_button)
        layout.addWidget(template_label)
        layout.addWidget(self.template_combo)
        layout.addWidget(self.compile_button)
        layout.addWidget(self.open_template_button)
        layout.addWidget(self.open_pdf_button)
        layout.addStretch(1)
        self.layout.addWidget(self.template_card)

    def _add_preview_card(self):
        self.preview_card = GenericImagesPreviewCard(parent=self.scrollWidget)
        self.preview_card.image_removed.connect(self._on_image_removed)
        self.layout.addWidget(self.preview_card)

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

    def _on_images_dropped(self, paths: list[str]):
        """处理拖拽或选择的图片"""
        self.images_path = paths
        self.preview_card.set_images(self.images_path)
        self.log_card.append_log(f"已选择 {len(self.images_path)} 张图片。")

    def _on_select_image_clicked(self):
        """点击选择图片按钮"""
        supported_exts = {"*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp"}
        project_root = str(Path(__file__).parent.parent.parent.parent)
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择要处理的图片",
            project_root,
            f"图片文件 ({' '.join(supported_exts)});;所有文件 (*.*)",
        )
        if paths:
            self.images_path = paths
            self.preview_card.set_images(self.images_path)
            self.log_card.append_log(f"已选择 {len(self.images_path)} 张图片。")

    def _on_image_removed(self, image_path: str):
        """处理图片预览中移除的图片"""
        if image_path in self.images_path:
            self.images_path.remove(image_path)
            self.log_card.append_log(f"已移除图片：{Path(image_path).name}")
            # 刷新预览框显示
            self.preview_card.set_images(self.images_path)

    def _on_start_clicked(self):
        if not self.images_path:
            show_message(self, "请先选择图片", MessageType.ERROR)
            return

        mode = {
            0: "extract_validate",
            1: "extract_only",
            2: "optimize",
        }[self.mode_combo.currentIndex()]
        self.log_card.append_log("=" * 30)
        self.log_card.append_log("开始执行模板区任务。")
        self._set_busy(True)
        self._set_manual_adjust_enabled(False)

        self._active_thread = TemplateWorkflowThread(self.images_path, mode, self._current_template_name())
        self._active_thread.log_message.connect(self.log_card.append_log)
        self._active_thread.task_finished.connect(self._on_template_workflow_finished)
        self._active_thread.start()

    def _on_compile_clicked(self):
        work_name = self._current_template_name()
        if not work_name:
            show_message(self, "请先选择模板", MessageType.ERROR)
            return

        self.log_card.append_log("=" * 30)
        self.log_card.append_log(f"开始编译验证模板：{work_name}.cls")
        self._set_busy(True)
        self._set_manual_adjust_enabled(False)

        self._active_thread = TemplateCompileThread(work_name)
        self._active_thread.log_message.connect(self.log_card.append_log)
        self._active_thread.task_finished.connect(self._on_source_compile_finished)
        self._active_thread.start()

    def _on_open_template_clicked(self):
        work_name = self._current_template_name()
        if work_name and work_name in self.template_path_map:
            open_in_explorer(self, self.template_path_map[work_name])
            return
        open_in_explorer(self, str(cls_dir()))

    def _on_open_pdf_clicked(self):
        if not self.current_pdf_path or not Path(self.current_pdf_path).exists():
            show_message(self, "当前没有可打开的 PDF", MessageType.ERROR)
            return
        open_in_explorer(self, self.current_pdf_path)

    def _on_import_template_clicked(self):
        """导入模板：复制cls文件到work/cls/"""
        cls_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择要导入的模板",
            "../",
            "LaTeX 模板 (*.cls);;所有文件 (*.*)",
        )
        if not cls_path:
            return

        # 复制到 work/cls/
        file_name = Path(cls_path).name
        dest_path = cls_dir() / file_name

        # 如果文件已存在，添加时间戳避免冲突
        if dest_path.exists():
            timestamp = create_work_name()
            base_name = Path(file_name).stem
            new_name = f"{base_name}_{timestamp}.cls"
            dest_path = cls_dir() / new_name

        shutil.copy2(cls_path, dest_path)

        self.log_card.append_log(f"已导入模板：{dest_path.name}")
        self._refresh_template_options()
        show_message(self, "导入成功", MessageType.SUCCESS)

    def _on_manual_adjust_start_clicked(self):
        """开始手动调整流程"""
        if not self.images_path:
            show_message(self, "请先选择图片", MessageType.ERROR)
            return

        feedback = self.feedback_input.text().strip()
        self.start_adjust_button.setEnabled(False)
        self.feedback_input.setEnabled(False)
        self._set_busy(True)

        qt_console = QtConsoleBridge()
        qt_console.log_message.connect(self.log_card.append_log)
        self._manual_adjust_service = WorkService(self.images_path, console=qt_console)

        self._active_thread = ManualAdjustThread(self._manual_adjust_service, feedback)
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
                # 发出信号,通知文档区有新模板生成
                self.template_generated.emit(work_name)
            self.current_pdf_path = result.get("pdf_path", "") or ""
            if self.current_pdf_path:
                self.log_card.append_log(f"已生成PDF：{Path(self.current_pdf_path).name}")
            show_message(self, "手动调整完成", MessageType.SUCCESS)
        else:
            message = payload.get("message", "调整失败") if isinstance(payload, dict) else str(payload)
            exception_type = payload.get("exception_type") if isinstance(payload, dict) else None
            self.log_card.append_log(message)
            show_message(self, get_user_facing_error_message(message, exception_type), MessageType.ERROR)

        self.start_adjust_button.setEnabled(True)
        self.feedback_input.setEnabled(True)

    def _on_template_workflow_finished(self, success: bool, payload: object):
        self._active_thread = None
        self._set_busy(False)
        self._set_manual_adjust_enabled(True)
        if success:
            result = payload if isinstance(payload, dict) else {}
            work_name = result.get("work_name", "")
            if work_name:
                self._refresh_template_options(work_name)
                # 发出信号,通知文档区有新模板生成
                self.template_generated.emit(work_name)
            if result.get("created"):
                self.log_card.append_log(f"已自动选中模板：{work_name}.cls")
            self.current_pdf_path = result.get("pdf_path", "") or ""
            show_message(self, "模板处理完成", MessageType.SUCCESS)
        else:
            message = payload.get("message", "处理失败") if isinstance(payload, dict) else str(payload)
            exception_type = payload.get("exception_type") if isinstance(payload, dict) else None
            self.log_card.append_log(message)
            show_message(self, get_user_facing_error_message(message, exception_type), MessageType.ERROR)

    def _on_source_compile_finished(self, success: bool, payload: object):
        self._active_thread = None
        self._set_busy(False)
        self._set_manual_adjust_enabled(True)
        if success:
            result = payload if isinstance(payload, dict) else {}
            self.current_pdf_path = result.get("pdf_path", "") or ""
            show_message(self, "编译成功", MessageType.SUCCESS)
        else:
            message = payload.get("message", "编译失败") if isinstance(payload, dict) else str(payload)
            exception_type = payload.get("exception_type") if isinstance(payload, dict) else None
            self.log_card.append_log(message)
            show_message(self, get_user_facing_error_message(message, exception_type), MessageType.ERROR)

    def _refresh_template_options(self, selected_name: str = ""):
        previous_name = selected_name or self._current_template_name()
        self.template_path_map = {
            template_path.stem: str(template_path)
            for template_path in list_template_files()
        }

        self.template_combo.clear()
        for template_name in self.template_path_map:
            self.template_combo.addItem(template_name)

        if previous_name:
            index = self.template_combo.findText(previous_name)
            if index >= 0:
                self.template_combo.setCurrentIndex(index)

    def _current_template_name(self) -> str:
        return self.template_combo.currentText().strip()

    def _set_busy(self, is_busy: bool):
        self.select_image_button.setEnabled(not is_busy)
        self.mode_combo.setEnabled(not is_busy)
        self.start_button.setEnabled(not is_busy)
        self.stop_button.setEnabled(is_busy)
        self.import_template_button.setEnabled(not is_busy)
        self.template_combo.setEnabled(not is_busy)
        self.compile_button.setEnabled(not is_busy)
        self.open_template_button.setEnabled(not is_busy)
        self.open_pdf_button.setEnabled(not is_busy)

    def _on_stop_clicked(self):
        """强行停止正在进行的任务"""
        if self._active_thread:
            self.log_card.append_log("用户请求停止任务...")
            self._active_thread.terminate()
            self._active_thread.wait()
            self._active_thread = None
            self._set_busy(False)
            self._set_manual_adjust_enabled(True)
            self.log_card.append_log("任务已停止")
            show_message(self, "任务已停止", MessageType.SUCCESS)

    def _set_manual_adjust_enabled(self, enabled: bool):
        """设置手动调整区的启用状态"""
        self.feedback_input.setEnabled(enabled)
        self.start_adjust_button.setEnabled(enabled)

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_template_options()

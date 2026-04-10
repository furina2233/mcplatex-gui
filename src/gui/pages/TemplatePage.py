import asyncio
import os
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QWidget
from qfluentwidgets import BodyLabel, CardWidget, ComboBox, LineEdit, PrimaryPushButton, PushButton

from src.gui.utils.ExplorerUtil import open_in_explorer
from src.gui.utils.MessageUtil import MessageType, show_message
from src.gui.utils.ScrollPageUtil import create_scrollable_page
from src.gui.widgets.GenericImagesPreviewCard import GenericImagesPreviewCard
from src.gui.widgets.TextLogCard import TextLogCard
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
from src.services.work_service import WorkService
from src.utils.cls_builder import build_cls_code

MAX_OPTIMIZATION_ROUNDS = 5


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
            self.task_finished.emit(False, {"message": str(exc)})

    async def _run_async(self):
        service = WorkService(self.image_paths)
        if self.mode in {"extract_validate", "extract_only"}:
            return await self._run_extract(service)
        return await self._run_optimize(service)

    async def _run_extract(self, service: WorkService):
        if self.mode == "extract_only":
            work_name = create_work_name()
            self.log_message.emit("开始提取图片内容并生成模板。")

            style_report, cls_output, tex_output = await service.generate_tex_and_cls(self.image_paths)
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
            self.log_message.emit(f"已生成模板：{work_name}.cls")
            self.log_message.emit("当前模式为仅提取，跳过编译验证。")
            return {"work_name": work_name, "pdf_path": "", "created": True}

        self.log_message.emit(f"开始执行一键提取并验证，最多进行 {MAX_OPTIMIZATION_ROUNDS} 轮视觉优化。")
        service.max_retries = MAX_OPTIMIZATION_ROUNDS
        result = await service.quick_generate(self.image_paths)
        self.log_message.emit(f"已生成模板：{result['work_name']}.cls")
        if result.get("success"):
            self.log_message.emit("视觉优化已完成。")
        else:
            self.log_message.emit(f"已达到最大优化次数 {MAX_OPTIMIZATION_ROUNDS}，输出当前最佳结果。")
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

        self.log_message.emit(f"开始对模板 {self.selected_template_name}.cls 做优化改进。")
        compile_result = await service.compile_files(cls_code, tex_code, job_name=self.selected_template_name)
        if compile_result.message.strip():
            self.log_message.emit(compile_result.message.strip())
        if not compile_result.pdf_generated or not compile_result.images:
            raise RuntimeError("优化前编译验证失败，无法继续优化。")

        self.log_message.emit(f"开始分析原图样式，最多进行 {MAX_OPTIMIZATION_ROUNDS} 轮优化。")
        style_report = await asyncio.to_thread(service.generation_service.analyze_style, self.image_paths)
        current_cls = cls_output
        current_cls_code = cls_code
        current_pdf_path = compile_result.pdf_path
        current_images = compile_result.images

        for attempt in range(1, MAX_OPTIMIZATION_ROUNDS + 1):
            revised_cls, audit_result = await service.optimize_after_compile(
                style_report,
                current_cls,
                self.image_paths[0],
                current_images[0],
            )
            if audit_result.passed:
                self.log_message.emit("当前模板已通过视觉审计，无需生成优化版本。")
                return {
                    "work_name": self.selected_template_name,
                    "pdf_path": current_pdf_path,
                    "created": False,
                }

            new_work_name = create_work_name()
            revised_cls = normalize_cls_output(revised_cls, class_name=new_work_name)
            revised_cls_code = build_cls_code(revised_cls)
            revised_tex_code = normalize_tex_documentclass(tex_code, new_work_name)

            save_work_item(
                new_work_name,
                revised_cls_code,
                revised_tex_code,
                cls_output=revised_cls,
                style_report=style_report,
                source_images=self.image_paths,
            )

            self.log_message.emit(f"开始第 {attempt}/{MAX_OPTIMIZATION_ROUNDS} 轮优化编译。")
            revised_compile_result = await service.compile_files(revised_cls_code, revised_tex_code, job_name=new_work_name)
            if revised_compile_result.message.strip():
                self.log_message.emit(revised_compile_result.message.strip())
            if not revised_compile_result.pdf_generated or not revised_compile_result.images:
                raise RuntimeError("优化后的模板编译失败。")

            current_cls = revised_cls
            current_cls_code = revised_cls_code
            current_pdf_path = revised_compile_result.pdf_path
            current_images = revised_compile_result.images
            self.log_message.emit(f"已生成优化模板：{new_work_name}.cls")

            current_tex = normalize_tex_documentclass(tex_code, new_work_name)
            tex_code = current_tex
            self.selected_template_name = new_work_name

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
            self.task_finished.emit(False, {"message": str(exc)})

    async def _run_async(self):
        cls_code, tex_code = load_work_item_sources(self.work_name)
        if not cls_code or not tex_code:
            raise RuntimeError("当前模板缺少对应的源文件。")

        service = WorkService([])
        compile_result = await service.compile_files(cls_code, tex_code, job_name=self.work_name)
        if compile_result.message.strip():
            self.log_message.emit(compile_result.message.strip())
        if not compile_result.pdf_generated:
            raise RuntimeError("编译失败")

        self.log_message.emit("编译验证完成。")
        return {"work_name": self.work_name, "pdf_path": compile_result.pdf_path}


class TemplatePage(QWidget):
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

    def _add_start_card(self):
        self.start_card = CardWidget(self.scrollWidget)
        layout = QHBoxLayout(self.start_card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.select_image_button = PushButton("选择图片", self.start_card)
        self.select_image_button.clicked.connect(self._on_select_images_clicked)

        self.mode_combo = ComboBox(self.start_card)
        self.mode_combo.addItems(["一键提取并验证", "仅提取", "优化改进"])
        self.mode_combo.setMinimumWidth(180)

        self.start_button = PrimaryPushButton("开始", self.start_card)
        self.start_button.clicked.connect(self._on_start_clicked)

        self.image_count_label = BodyLabel("未选择图片", self.start_card)

        layout.addWidget(self.select_image_button)
        layout.addWidget(self.mode_combo)
        layout.addWidget(self.start_button)
        layout.addStretch(1)
        layout.addWidget(self.image_count_label)
        self.layout.addWidget(self.start_card)

    def _add_template_card(self):
        self.template_card = CardWidget(self.scrollWidget)
        layout = QHBoxLayout(self.template_card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.template_combo = ComboBox(self.template_card)
        self.template_combo.setMinimumWidth(240)

        self.compile_button = PushButton("编译验证", self.template_card)
        self.compile_button.clicked.connect(self._on_compile_clicked)

        self.open_template_button = PushButton("打开模板", self.template_card)
        self.open_template_button.clicked.connect(self._on_open_template_clicked)

        self.open_pdf_button = PushButton("打开PDF", self.template_card)
        self.open_pdf_button.clicked.connect(self._on_open_pdf_clicked)

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
        self.manual_adjust_card = CardWidget(self.scrollWidget)
        layout = QHBoxLayout(self.manual_adjust_card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.manual_adjust_input = LineEdit(self.manual_adjust_card)
        self.manual_adjust_input.setPlaceholderText("输入手动调整指令，暂无后端入口")

        self.manual_adjust_button = PushButton("调整", self.manual_adjust_card)
        self.manual_adjust_button.clicked.connect(self._on_manual_adjust_clicked)

        layout.addWidget(self.manual_adjust_input)
        layout.addWidget(self.manual_adjust_button)
        self.layout.addWidget(self.manual_adjust_card)

    def _on_select_images_clicked(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择要处理的图片",
            "../",
            "图片文件 (*.png *.jpg *.jpeg);;所有文件 (*.*)",
        )
        if not paths:
            return

        self.images_path = paths
        self.preview_card.set_images(self.images_path)
        self.image_count_label.setText(f"已选择 {len(self.images_path)} 张图片")
        self.log_card.append_log(f"已选择 {len(self.images_path)} 张图片。")
        show_message(self, "选择成功", MessageType.SUCCESS)

    def _on_image_removed(self, path: str):
        self.images_path = [item for item in self.images_path if item != path]
        self.preview_card.set_images(self.images_path)
        if self.images_path:
            self.image_count_label.setText(f"已选择 {len(self.images_path)} 张图片")
        else:
            self.image_count_label.setText("未选择图片")

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

    def _on_manual_adjust_clicked(self):
        instruction = self.manual_adjust_input.text().strip()
        if not instruction:
            show_message(self, "请输入调整内容", MessageType.ERROR)
            return

        self.log_card.append_log(f"手动调整请求暂未接入后端，已跳过：{instruction}")
        show_message(self, "暂无后端入口", MessageType.ERROR)

    def _on_template_workflow_finished(self, success: bool, payload: object):
        self._active_thread = None
        self._set_busy(False)
        if success:
            result = payload if isinstance(payload, dict) else {}
            work_name = result.get("work_name", "")
            if work_name:
                self._refresh_template_options(work_name)
            if result.get("created"):
                self.log_card.append_log(f"已自动选中模板：{work_name}.cls")
            self.current_pdf_path = result.get("pdf_path", "") or ""
            show_message(self, "模板处理完成", MessageType.SUCCESS)
        else:
            message = payload.get("message", "处理失败") if isinstance(payload, dict) else str(payload)
            self.log_card.append_log(message)
            show_message(self, "模板处理失败", MessageType.ERROR)

    def _on_source_compile_finished(self, success: bool, payload: object):
        self._active_thread = None
        self._set_busy(False)
        if success:
            result = payload if isinstance(payload, dict) else {}
            self.current_pdf_path = result.get("pdf_path", "") or ""
            show_message(self, "编译成功", MessageType.SUCCESS)
        else:
            message = payload.get("message", "编译失败") if isinstance(payload, dict) else str(payload)
            self.log_card.append_log(message)
            show_message(self, "编译失败", MessageType.ERROR)

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
        self.template_combo.setEnabled(not is_busy)
        self.compile_button.setEnabled(not is_busy)
        self.open_template_button.setEnabled(not is_busy)
        self.open_pdf_button.setEnabled(not is_busy)
        self.manual_adjust_button.setEnabled(not is_busy)

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_template_options()

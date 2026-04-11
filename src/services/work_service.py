import asyncio
from typing import List

from rich.console import Console

from agents import create_cls_generator_agent, create_semantic_extractor_agent, create_style_analyzer_agent
from agents.cls_inspector import create_cls_inspector_agent
from agents.combined_inspector import create_combined_inspector_agent
from agents.debugger_agent import create_debugger_agent
from agents.img_recognizer import create_img_recognizer_agent
from agents.tex_inspector import create_tex_inspector_agent
from agents.visual_auditor import create_visual_auditor_agent
from agents.manual_adjustor import create_manual_adjustor_agent, ManualAdjustorInput
from llm_client import (
    TEXT_MODEL,
    VISUAL_MODEL,
    text_async_client,
    text_client,
    visual_async_client,
    visual_client,
)
from services.compilation_service import CompilationService
from services.generation_service import GenerationService
from services.optimization_service import OptimizationService
from services.workflow_support import (
    create_work_name,
    normalize_tex_documentclass,
    normalize_cls_output,
    save_final_results,
    save_iteration_snapshot,
    write_working_sources,
)
from utils.cls_builder import build_cls_code
from utils.settings_manager import get_setting


class GenerateFilesService(GenerationService):
    pass


class CompileFilesService(CompilationService):
    pass


class OptimizeFilesService(OptimizationService):
    pass


class WorkService:
    def __init__(self, pic_paths: List[str], max_retries: int | None = None, console: Console | None = None):
        self.pic_paths = list(pic_paths)
        self.max_retries = max_retries if max_retries is not None else get_setting("max_retries", 5)
        self.console = console or Console()

        self.style_agent = create_style_analyzer_agent(visual_client, VISUAL_MODEL)
        self.cls_agent = create_cls_generator_agent(text_async_client, TEXT_MODEL)
        self.tex_agent = create_semantic_extractor_agent(visual_async_client, VISUAL_MODEL)
        self.debugger_agent = create_debugger_agent(text_client, TEXT_MODEL)
        self.visual_auditor_agent = create_visual_auditor_agent(visual_client, VISUAL_MODEL)
        self.tex_inspector_agent = create_tex_inspector_agent(text_client, TEXT_MODEL)
        self.cls_inspector_agent = create_cls_inspector_agent(text_client, TEXT_MODEL)
        self.combined_inspector_agent = create_combined_inspector_agent(text_client, TEXT_MODEL)
        self.img_recognizer_agent = create_img_recognizer_agent(visual_client, VISUAL_MODEL)
        self.manual_adjustor_agent = create_manual_adjustor_agent(text_async_client, TEXT_MODEL)

        self.generation_service = GenerateFilesService(
            style_agent=self.style_agent,
            cls_agent=self.cls_agent,
            tex_agent=self.tex_agent,
            console=self.console,
        )
        self.compilation_service = CompileFilesService(
            debugger_agent=self.debugger_agent,
            cls_inspector_agent=self.cls_inspector_agent,
            tex_inspector_agent=self.tex_inspector_agent,
            console=self.console,
        )
        self.optimization_service = OptimizeFilesService(
            visual_auditor_agent=self.visual_auditor_agent,
            cls_agent=self.cls_agent,
            console=self.console,
        )

        # 用于手动调整的状态
        self._work_name: str | None = None
        self._style_report = None
        self._current_cls = None
        self._current_tex = None
        self._current_cls_code: str = ""
        self._current_tex_code: str = ""
        self._final_images: list[dict[str, str]] = []
        self._attempt: int = 0

    async def generate_tex_and_cls(self, image_paths: List[str] | None = None):
        paths = list(image_paths or self.pic_paths)
        return await self.generation_service.generate(paths)

    async def compile_files(self, cls_code: str, tex_code: str, job_name: str = "template"):
        return await self.compilation_service.compile(cls_code, tex_code, job_name=job_name)

    async def repair_failed_compile(self, error_log: str, cls_code: str, tex_code: str, job_name: str = "template"):
        return await self.compilation_service.repair_failed_sources(error_log, cls_code, tex_code, job_name=job_name)

    async def optimize_after_compile(self, style_report, cls_output, original_path: str, rendered_image: dict[str, str]):
        return await self.optimization_service.optimize(style_report, cls_output, original_path, rendered_image)

    async def quick_generate(self, image_paths: List[str] | None = None):
        if image_paths is not None:
            self.pic_paths = list(image_paths)
        if not self.pic_paths:
            raise ValueError("No input images were provided.")

        work_name = create_work_name()
        style_report, current_cls, current_tex = await self.generate_tex_and_cls(self.pic_paths)
        self.console.print("已生成 tex 文件")
        self.console.print("已生成 cls 文件")
        current_cls = normalize_cls_output(current_cls, class_name=work_name)
        current_cls_code = build_cls_code(current_cls)
        current_tex_code = normalize_tex_documentclass(current_tex.tex_code, work_name)

        final_images: list[dict[str, str]] = []
        is_success = False

        for attempt in range(1, self.max_retries + 1):
            self.console.print(f"迭代循环 ({attempt}/{self.max_retries})")
            write_working_sources(work_name, current_cls_code, current_tex_code)
            save_iteration_snapshot(work_name, attempt, current_cls_code, current_tex_code)

            compile_result = await self.compile_files(current_cls_code, current_tex_code, job_name=work_name)
            if not compile_result.pdf_generated:
                repair_result = await self.repair_failed_compile(
                    compile_result.message,
                    current_cls_code,
                    current_tex_code,
                    job_name=work_name,
                )
                current_cls_code = repair_result.cls_code
                current_tex_code = repair_result.tex_code
                current_tex.tex_code = current_tex_code
                continue

            self.console.print("编译成功")
            final_images = compile_result.images
            if not final_images:
                is_success = True
                break

            revised_cls, audit_result = await self.optimize_after_compile(
                style_report,
                current_cls,
                self.pic_paths[0],
                final_images[0],
            )
            if audit_result.passed:
                is_success = True
                break

            current_cls = normalize_cls_output(revised_cls, class_name=work_name)
            current_cls_code = build_cls_code(current_cls)

        current_tex.tex_code = current_tex_code
        save_final_results(
            work_name,
            current_cls,
            current_tex,
            current_cls_code,
            current_tex_code,
            final_images,
            style_report=style_report,
            source_images=self.pic_paths,
        )

        if not is_success:
            self.console.print("已达到最大重试次数")

        return {
            "style_report": style_report,
            "cls_output": current_cls,
            "tex_output": current_tex,
            "cls_code": current_cls_code,
            "tex_code": current_tex_code,
            "images": final_images,
            "success": is_success,
            "work_name": work_name,
            "pdf_path": compile_result.pdf_path if final_images is not None else "",
        }

    async def run_async(self):
        return await self.quick_generate()

    def run(self):
        return asyncio.run(self.quick_generate())

    async def start_manual_adjustment(self, image_paths: List[str] | None = None):
        """初始化手动调整流程，生成初始代码但不自动迭代"""
        paths = list(image_paths or self.pic_paths)
        if not paths:
            raise ValueError("No input images were provided.")

        self._work_name = create_work_name()
        self._style_report, self._current_cls, self._current_tex = await self.generate_tex_and_cls(paths)
        self.console.print("已生成 tex 文件")
        self.console.print("已生成 cls 文件")
        self._current_cls = normalize_cls_output(self._current_cls, class_name=self._work_name)
        self._current_cls_code = build_cls_code(self._current_cls)
        self._current_tex_code = normalize_tex_documentclass(self._current_tex.tex_code, self._work_name)
        self._final_images = []
        self._attempt = 0

        write_working_sources(self._work_name, self._current_cls_code, self._current_tex_code)
        save_iteration_snapshot(self._work_name, 0, self._current_cls_code, self._current_tex_code)

        return {
            "work_name": self._work_name,
            "cls_code": self._current_cls_code,
            "tex_code": self._current_tex_code,
            "attempt": self._attempt,
        }

    async def manual_iterate(self, user_feedback: str = ""):
        """执行一次手动迭代，根据用户反馈调整代码（纯文本模式，不使用视觉模型）"""
        if self._work_name is None:
            raise ValueError("请先调用 start_manual_adjustment 初始化手动调整流程。")

        self._attempt += 1
        self.console.print(f"迭代循环 ({self._attempt})")

        write_working_sources(self._work_name, self._current_cls_code, self._current_tex_code)
        save_iteration_snapshot(self._work_name, self._attempt, self._current_cls_code, self._current_tex_code)

        compile_result = await self.compile_files(self._current_cls_code, self._current_tex_code, job_name=self._work_name)
        if not compile_result.pdf_generated:
            # 编译失败：使用文本inspector修复代码
            self.console.print("编译失败，正在尝试修复...")
            repair_result = await self.repair_failed_compile(
                compile_result.message,
                self._current_cls_code,
                self._current_tex_code,
                job_name=self._work_name,
            )
            self._current_cls_code = repair_result.cls_code
            self._current_tex_code = repair_result.tex_code
            self._current_tex.tex_code = self._current_tex_code
        else:
            self.console.print("编译成功")
            self._final_images = compile_result.images

            # 手动调整模式：根据用户反馈使用文本模型修改代码（不使用视觉审计）
            if user_feedback:
                self.console.print(f"根据用户反馈修改代码：{user_feedback}")
                try:
                    # 使用专门的手动调整Agent
                    adjustor_input = ManualAdjustorInput(
                        user_feedback=user_feedback,
                        cls_code=self._current_cls_code,
                        tex_code=self._current_tex_code,
                    )
                    
                    revised_output = await asyncio.to_thread(
                        self.manual_adjustor_agent.run, adjustor_input
                    )
                    
                    # 更新代码
                    self._current_cls_code = revised_output.cls_code_after
                    self._current_tex_code = revised_output.tex_code_after
                    self._current_tex.tex_code = self._current_tex_code
                    
                    if revised_output.explanation:
                        self.console.print(f"修改说明：{revised_output.explanation}")
                    self.console.print("已根据用户反馈修改代码")
                    
                except Exception as e:
                    self.console.print(f"代码修改失败：{e}，继续使用当前代码")

        save_final_results(
            self._work_name,
            self._current_cls,
            self._current_tex,
            self._current_cls_code,
            self._current_tex_code,
            self._final_images,
            style_report=self._style_report,
            source_images=self.pic_paths,
        )

        return {
            "cls_code": self._current_cls_code,
            "tex_code": self._current_tex_code,
            "images": self._final_images,
            "attempt": self._attempt,
            "success": bool(self._final_images),
            "work_name": self._work_name,
            "pdf_path": compile_result.pdf_path if compile_result.pdf_generated else "",
        }

    def get_current_state(self) -> dict:
        """获取当前手动调整状态"""
        return {
            "work_name": self._work_name,
            "cls_code": self._current_cls_code,
            "tex_code": self._current_tex_code,
            "images": self._final_images,
            "attempt": self._attempt,
        }



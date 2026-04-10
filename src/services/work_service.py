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


class GenerateFilesService(GenerationService):
    pass


class CompileFilesService(CompilationService):
    pass


class OptimizeFilesService(OptimizationService):
    pass


class WorkService:
    def __init__(self, pic_paths: List[str], max_retries: int = 5, console: Console | None = None):
        self.pic_paths = list(pic_paths)
        self.max_retries = max_retries
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

        self.console.print("[bold green]正在启动 LaTeX 逆向工作流...[/bold green]")

        work_name = create_work_name()
        style_report, current_cls, current_tex = await self.generate_tex_and_cls(self.pic_paths)
        current_cls = normalize_cls_output(current_cls, class_name=work_name)
        current_cls_code = build_cls_code(current_cls)
        current_tex_code = normalize_tex_documentclass(current_tex.tex_code, work_name)

        final_images: list[dict[str, str]] = []
        is_success = False

        for attempt in range(1, self.max_retries + 1):
            self.console.print(f"\n[bold blue]迭代循环 ({attempt}/{self.max_retries})[/bold blue]")
            write_working_sources(work_name, current_cls_code, current_tex_code)
            save_iteration_snapshot(work_name, attempt, current_cls_code, current_tex_code)

            compile_result = await self.compile_files(current_cls_code, current_tex_code, job_name=work_name)
            if not compile_result.pdf_generated:
                self.console.print("[bold red]编译失败，进入定向修复。[/bold red]")
                repair_result = await self.repair_failed_compile(
                    compile_result.message,
                    current_cls_code,
                    current_tex_code,
                    job_name=work_name,
                )
                current_cls_code = repair_result.cls_code
                current_tex_code = repair_result.tex_code
                current_tex.tex_code = current_tex_code
                self.console.print(f"[yellow]已重生成并覆盖 {repair_result.target_file}，开始下一轮编译。[/yellow]")
                continue

            self.console.print("[bold green]编译成功。[/bold green]")
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

            self.console.print("[yellow]视觉审计未通过，重新生成 CLS 后继续。[/yellow]")
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
            self.console.print("[red]❌ 已达到最大重试次数，流程结束。[/red]")

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



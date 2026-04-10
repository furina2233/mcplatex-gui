import asyncio
from dataclasses import dataclass

from agents.cls_inspector import CLSInspectorInput, CLSInspectorOutput
from agents.debugger_agent import DebuggerInput, DebuggerOutput
from agents.tex_inspector import TexInspectorInput, TexInspectorOutput
from latex_build_and_preview import build_and_preview
from services.workflow_support import (
    extract_documentclass_name,
    normalize_latex_source,
    normalize_tex_documentclass,
    overwrite_working_source,
)


@dataclass
class CompileResult:
    pdf_generated: bool
    message: str
    images: list[dict[str, str]]
    pdf_path: str = ""
    log_path: str = ""
    job_name: str = ""


@dataclass
class RepairResult:
    cls_code: str
    tex_code: str
    target_file: str
    debug_result: DebuggerOutput


class CompilationService:
    def __init__(self, debugger_agent, cls_inspector_agent, tex_inspector_agent, console):
        self.debugger_agent = debugger_agent
        self.cls_inspector_agent = cls_inspector_agent
        self.tex_inspector_agent = tex_inspector_agent
        self.console = console

    async def compile(self, cls_code: str, tex_code: str, job_name: str = "template") -> CompileResult:
        pdf_generated, message, images, artifacts = await build_and_preview(cls_code, tex_code, job_name=job_name)
        return CompileResult(
            pdf_generated=pdf_generated,
            message=message,
            images=images,
            pdf_path=artifacts.get("pdf_path", ""),
            log_path=artifacts.get("log_path", ""),
            job_name=artifacts.get("job_name", job_name),
        )

    async def repair_failed_sources(self, error_log: str, cls_code: str, tex_code: str, job_name: str = "template") -> RepairResult:
        log_snippet = error_log[-3000:] if len(error_log) > 3000 else error_log
        debugger_input = DebuggerInput(
            error_log=log_snippet,
            cls_snippet=cls_code[:1000],
            tex_snippet=tex_code[:1000],
        )
        debug_result: DebuggerOutput = await asyncio.to_thread(self.debugger_agent.run, debugger_input)

        error_feedback = self._build_error_feedback(debug_result, log_snippet)
        if debug_result.target_agent == "cls_generator":
            repair_input = CLSInspectorInput(
                cls_doc=cls_code,
                error_feedback=error_feedback,
            )
            repaired_cls: CLSInspectorOutput = await asyncio.to_thread(self.cls_inspector_agent.run, repair_input)
            cls_code = normalize_latex_source(repaired_cls.cls_doc_after)
            overwrite_working_source(job_name, "cls", cls_code)
            return RepairResult(cls_code=cls_code, tex_code=tex_code, target_file="template.cls", debug_result=debug_result)

        repair_input = TexInspectorInput(
            tex_doc=tex_code,
            error_feedback=error_feedback,
        )
        repaired_tex: TexInspectorOutput = await asyncio.to_thread(self.tex_inspector_agent.run, repair_input)
        class_name = extract_documentclass_name(tex_code, default=job_name)
        tex_code = normalize_tex_documentclass(repaired_tex.tex_doc_after, class_name)
        overwrite_working_source(job_name, "tex", tex_code)
        return RepairResult(cls_code=cls_code, tex_code=tex_code, target_file="main.tex", debug_result=debug_result)

    def _build_error_feedback(self, debug_result: DebuggerOutput, error_log: str) -> str:
        target_file = "template.cls" if debug_result.target_agent == "cls_generator" else "main.tex"
        return (
            f"Error summary: {debug_result.error_summary}\n"
            f"Target file: {target_file}\n"
            f"Fix instruction: {debug_result.fix_instruction}\n\n"
            f"Compiler log tail:\n{error_log}"
        )

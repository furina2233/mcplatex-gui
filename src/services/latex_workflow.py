import os
import asyncio
import traceback
import base64
import re
import copy
from typing import List

import instructor
from rich.console import Console

from agents.cls_inspector import CLSInspectorInput
from agents.combined_inspector import CombinedInspectorInput
from agents.img_recognizer import ImgRecognizerInput
from latex_build_and_preview import LatexEnvironmentError, build_and_preview
from schemas import HeaderFooterSettings, ParagraphSettings, CaptionSettings, SectionSettings, AbstractSettings, \
    AuthorSettings, GeometrySettings, FontSettings, TitleSettings
# 导入工具和异常
from utils.cls_builder import build_cls_code

# 导入 Agent 输入/输出模型 (Data Models)
from agents.style_analyzer import StyleAnalysisInput, StyleAnalysisReport
from agents.cls_generator import CLSGeneratorInput, CLSGeneratorOutput
from agents.semantic_extractor import SemanticExtractorInput, SemanticExtractorOutput
from agents.debugger_agent import DebuggerInput, DebuggerOutput
from agents.visual_auditor import VisualAuditorInput, VisualAuditorOutput
from agents.tex_inspector import TexInspectorInput, TexInspectorOutput
from schemas.style_schema import FontFeature, PageLayout, SpacingFeature


class LatexReverseEngineeringService:
    def __init__(
        self,
        style_agent,
        cls_agent,
        tex_agent,
        debugger_agent,
        visual_auditor_agent,
        tex_inspector_agent,
        cls_inspector_agent,
        combined_inspector_agent,
        img_recognizer_agent,
        max_retries: int = 5,
    ):
        """
        初始化服务，注入所有需要的 Agent。
        """
        self.style_agent = style_agent
        self.cls_agent = cls_agent
        self.tex_agent = tex_agent
        self.debugger_agent = debugger_agent
        self.visual_auditor_agent = visual_auditor_agent
        self.tex_inspector_agent = tex_inspector_agent
        self.cls_inspector_agent = cls_inspector_agent
        self.combined_inspector_agent = combined_inspector_agent
        self.img_recognizer_agent = img_recognizer_agent
        self.max_retries = max_retries
        self.console = Console()

    # ==================================================
    # 主流程控制 (Orchestrator)
    # ==================================================

    async def run(self, base_dir: str, image_paths: List[str]):
        """执行主要的逆向工程工作流"""
        self.console.print(f"[bold green]正在启动 LaTeX 逆向工程系统 ...[/bold green]")

        try:
            # 1. 准备环境
            if image_paths is None:
                image_paths = self._get_image_paths(base_dir)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_dir = os.path.join(project_root, "temp")

            # 2. 阶段一：样式分析 (Sync Call)
            style_report = self._analyze_style(image_paths)
            cls_output, tex_output = await self._generate_initial_code(
                image_paths, style_report
            )

            # # 4. 阶段三：TEX 代码语法检查 (Sync Call)
            # tex_inspector_output = self._inspect_tex_code(tex_output)



            # # 6. 阶段四：CLS 代码语法检查 (Sync Call)
            # cls_inspector_output = self._inspect_cls_code(cls_output)

            # 4. 阶段三：同时进行TEX和CLS代码语法检查 (Async Concurrent)
            self.console.rule("[bold cyan]阶段三：代码语法检查[/bold cyan]")
            # 使用asyncio.gather并行执行两个检查任务
            # tex_inspector_output, cls_inspector_output = await asyncio.gather(
            #     self._async_inspect_tex_code(tex_output),
            #     self._async_inspect_cls_code(cls_output)
            # )
            # 暂时禁用语法检查
            #tex_inspector_output, cls_inspector_output = await self._async_inspect_combined_code(tex_output, cls_output)

            print("暂时禁用语法检查")
            tex_inspector_output = tex_output
            cls_inspector_output = cls_output


            # 5. 阶段四：编译与修复循环 (Async Loop)
            # 包含：编译错误修复 + 视觉差异修正
            final_cls, final_tex, images, is_success = await self._compile_and_refine(
                cls_inspector_output, tex_inspector_output, style_report, image_paths
            )

            # 5. 保存结果
            self._save_final_results(
                output_dir, final_cls, final_tex, images, is_success
            )

        except Exception as e:
            self.console.print(f"[bold red]运行出错:[/bold red] {str(e)}")
            traceback.print_exc()

    # ==================================================
    # 业务逻辑原子步骤
    # ==================================================

    def _analyze_style(self, image_paths: list[str]) -> StyleAnalysisReport:
        """阶段一：分析视觉样式 (同步调用)"""
        self.console.rule("[bold cyan]阶段一：样式分析[/bold cyan]")

        style_input = StyleAnalysisInput(
            instruction_text=(
                "Analyze the provided paper screenshots and estimate structured layout parameters. "
                "You must identify margins, column count, column gap, header height, header-to-text spacing, "
                "footer spacing, paragraph indent, body line spacing, paragraph spacing, section and subsection "
                "spacing, title/author/abstract spacing, caption spacing, and representative font/alignment features."
            ),
            images=[instructor.Image.from_path(path) for path in image_paths],
        )

        self.console.print("[cyan]Agent 1 正在分析视觉样式...[/cyan]")
        # Style Agent 使用同步 Client，直接调用 .run()
        style_report = self.style_agent.run(style_input)
        self.console.print("[green]✅ 样式分析完成！[/green]")
        return style_report

    async def _generate_initial_code(
        self, image_paths: list[str], style_report: StyleAnalysisReport
    ) -> tuple[CLSGeneratorOutput, SemanticExtractorOutput]:
        """阶段二：并发生成初始代码 (异步并发)"""
        self.console.rule("[bold cyan]阶段二：并发生成 CLS 和 TEX[/bold cyan]")

        cls_input = CLSGeneratorInput(
            mode="initial",
            style_report=style_report,
        )

        tex_input = SemanticExtractorInput(
            mode="initial",
            instruction_text=(
                "请从这些论文截图中提取文本内容，生成 .tex 文件。\n\n"
                "【图片/表格处理】完全忽略内部内容，只提取 caption，用占位符替代。\n"
                "【禁止】使用 \\textbf, \\Large, \\vspace 等样式命令。"
                "Only transcribe content that is clearly visible in the images. If the last sentence is cut off, stop there and do not complete it. Do not invent figures, tables, captions, references, a References section, a thebibliography environment, or a bibliography command unless they are clearly visible.\n"
            ),
            images=[instructor.Image.from_path(p) for p in image_paths],
        )

        self.console.print("[yellow]🚀 正在生成初始代码...[/yellow]")

        # CLS 和 TEX Agent 使用异步 Client，调用 .run_async() 并发执行
        cls_output, tex_output = await asyncio.gather(
            self.cls_agent.run_async(cls_input),
            self.tex_agent.run_async(tex_input),
        )

        self.console.print("[green]✅ 初始代码生成完成！[/green]")
        cls_output = self._normalize_cls_output(cls_output)
        return cls_output, tex_output

    async def _compile_and_refine(
        self,
        cls_output: CLSGeneratorOutput,
        tex_output: SemanticExtractorOutput,
        style_report: StyleAnalysisReport,
        image_paths: list[str],
    ):
        """阶段三：智能编译验证 -> 视觉审计 -> 修复循环"""
        self.console.rule("[bold cyan]阶段三：智能编译验证与视觉精修[/bold cyan]")

        current_cls = cls_output
        current_tex = tex_output
        final_images = []
        is_finished = False  # 标记是否完全完成（编译成功且视觉通过）

        # 循环计数器
        attempt = 0

        while attempt < self.max_retries:
            attempt += 1
            self.console.print(
                f"\n[bold blue]🔄 迭代循环 (第 {attempt}/{self.max_retries} 次)...[/bold blue]"
            )

            # 1. 准备代码
            current_cls = self._normalize_cls_output(current_cls)
            cls_code = build_cls_code(current_cls)
            tex_code = self._normalize_tex_documentclass(current_tex.tex_code)
            current_tex = SemanticExtractorOutput(tex_code=tex_code)
            self._save_iteration_snapshot(attempt, cls_code, tex_code)

            # 2. 调用 MCP 工具进行编译 (Async)
            try:
                pdf_generated, msg, images = await build_and_preview(cls_code, tex_code)
            except LatexEnvironmentError as env_err:
                self.console.print(
                    f"\n[bold red]⛔ 严重环境错误，程序终止！[/bold red]"
                )
                self.console.print(f"[red]原因: {str(env_err)}[/red]")
                raise env_err

            # =========================================================
            # 分支 A: 编译失败 -> 调用 Debugger Agent
            # =========================================================
            if not pdf_generated:
                self.console.print(f"[bold red]❌ 编译失败 (代码错误)！[/bold red]")
                log_preview = msg[-1000:] if len(msg) > 1000 else msg
                self.console.print(f"[dim]Log Tail: ...{log_preview}[/dim]")

                # 诊断并修复
                current_cls, current_tex = await self._handle_compilation_error(
                    error_log=msg,
                    cls_output=current_cls,
                    tex_output=current_tex,
                    style_report=style_report,
                    image_paths=image_paths,
                )
                # 修复后直接进入下一次循环进行验证
                continue

            self.console.print(
                "[bold green]✅ 本轮编译已生成 PDF，进入渲染对比审计阶段...[/bold green]"
            )
            final_images = images

            if not images:
                self.console.print(
                    "[yellow]⚠️ 本轮编译已生成 PDF，但未生成预览图，跳过渲染对比审计。[/yellow]"
                )
                is_finished = True
                break

            try:
                audit_result = self._perform_render_comparison_audit(
                    original_path=image_paths[0],
                    rendered_image=images[0],
                    cls_output=current_cls,
                )

                if audit_result.passed:
                    self.console.print(
                        "[bold green]🏁 渲染对比审计通过，复刻完成。[/bold green]"
                    )
                    is_finished = True
                    break
                else:
                    self.console.print(
                        "[bold yellow]⚠️ 渲染对比审计未通过，需要继续调整版式。[/bold yellow]"
                    )
                    self.console.print(f"[dim]反馈意见:\n{audit_result.feedback}[/dim]")

                    self.console.print(
                        "🔧 正在请求 [bold]Agent 2 (CLS)[/bold] 根据渲染对比反馈调整参数..."
                    )
                    new_cls_input = CLSGeneratorInput(
                        mode="revision",
                        style_report=style_report,
                        revision_feedback=f"Render Comparison Audit Failed. Feedback: {audit_result.feedback}",
                        previous_config=current_cls,
                    )
                    current_cls = self._normalize_cls_output(
                        await self.cls_agent.run_async(new_cls_input)
                    )
                    continue

            except Exception as e:
                self.console.print(f"[red]渲染对比审计阶段发生错误: {e}[/red]")
                is_finished = True
                break

        if not is_finished:
            self.console.print("[red]❌ 已达到最大重试次数，停止优化。[/red]")

        return current_cls, current_tex, final_images, is_finished

    def _perform_render_comparison_audit(
        self,
        original_path: str,
        rendered_image: dict[str, str],
        cls_output: CLSGeneratorOutput,
    ) -> VisualAuditorOutput:
        """Compare the rendered PDF page against the original screenshot and request field-level fixes."""
        comparison_summary = self._build_page_comparison_summary(
            original_path,
            rendered_image["path"],
        )
        audit_input = VisualAuditorInput(
            images=[
                instructor.Image.from_path(original_path),
                instructor.Image.from_path(rendered_image["path"]),
            ],
            instruction_text=(
                "Compare the original paper screenshot with the rendered PDF page. "
                "Focus only on layout, margins, header/footer placement, spacing, fonts, title/abstract/section block geometry, "
                "and whether the rendered page contains hallucinated trailing content not present in the original image. "
                "Ignore OCR wording mistakes. Return only field-level feedback that maps to the CLS generator schema.\n\n"
                f"Local comparison summary:\n{comparison_summary}\n\n"
                f"Current CLS configuration:\n{cls_output.model_dump_json(indent=2)}"
            ),
        )
        return self.visual_auditor_agent.run(audit_input)

    def _build_page_comparison_summary(self, original_path: str, rendered_path: str) -> str:
        """Build a compact local comparison summary to stabilize the multimodal audit."""
        original_metrics = self._estimate_page_metrics(original_path)
        rendered_metrics = self._estimate_page_metrics(rendered_path)

        lines = [
            "Use these metrics as hints only; the images remain the source of truth.",
            self._format_metrics("Original", original_metrics),
            self._format_metrics("Rendered", rendered_metrics),
        ]

        if original_metrics.get("content_bottom_ratio") and rendered_metrics.get("content_bottom_ratio"):
            delta = rendered_metrics["content_bottom_ratio"] - original_metrics["content_bottom_ratio"]
            if isinstance(delta, float) and delta > 0.06:
                lines.append(
                    "Heuristic warning: rendered content extends noticeably lower than the original page and may contain extra trailing material."
                )

        return "\n".join(lines)

    def _estimate_page_metrics(self, image_path: str) -> dict[str, float | int | str | None]:
        """Estimate simple page layout metrics from an image using a white-background heuristic."""
        try:
            from PIL import Image
        except ImportError:
            return {"path": image_path, "error": "Pillow unavailable"}

        with Image.open(image_path) as img:
            gray = img.convert("L")
            width, height = gray.size
            mask = gray.point(lambda p: 255 if p < 245 else 0, mode="L")
            bbox = mask.getbbox()

            metrics: dict[str, float | int | str | None] = {
                "path": image_path,
                "width": width,
                "height": height,
                "aspect_ratio": round(width / height, 4) if height else None,
                "content_bbox": None,
                "top_margin_ratio": None,
                "bottom_margin_ratio": None,
                "left_margin_ratio": None,
                "right_margin_ratio": None,
                "content_bottom_ratio": None,
                "column_gap_ratio": None,
            }

            if not bbox:
                return metrics

            left, top, right, bottom = bbox
            metrics["content_bbox"] = f"({left},{top})-({right},{bottom})"
            metrics["top_margin_ratio"] = round(top / height, 4) if height else None
            metrics["bottom_margin_ratio"] = round((height - bottom) / height, 4) if height else None
            metrics["left_margin_ratio"] = round(left / width, 4) if width else None
            metrics["right_margin_ratio"] = round((width - right) / width, 4) if width else None
            metrics["content_bottom_ratio"] = round(bottom / height, 4) if height else None
            metrics["column_gap_ratio"] = self._detect_column_gap(mask, width, height)
            return metrics

    def _detect_column_gap(self, mask_image, width: int, height: int) -> float | None:
        """Estimate a central column gap ratio using the rendered binary mask."""
        if not width or not height:
            return None

        band_top = int(height * 0.25)
        band_bottom = int(height * 0.8)
        band_height = max(1, band_bottom - band_top)
        center_start = int(width * 0.2)
        center_end = int(width * 0.8)
        pixels = mask_image.load()
        low_ink_threshold = max(3, int(band_height * 0.01))

        longest_run = 0
        current_run = 0
        for x in range(center_start, center_end):
            ink_pixels = 0
            for y in range(band_top, band_bottom):
                if pixels[x, y] != 0:
                    ink_pixels += 1
            if ink_pixels <= low_ink_threshold:
                current_run += 1
                longest_run = max(longest_run, current_run)
            else:
                current_run = 0

        if longest_run < max(8, int(width * 0.02)):
            return None
        return round(longest_run / width, 4)

    def _format_metrics(self, label: str, metrics: dict[str, float | int | str | None]) -> str:
        """Format metrics for the audit prompt."""
        parts = [f"{label} metrics:"]
        for key, value in metrics.items():
            parts.append(f"- {key}: {value}")
        return "\n".join(parts)

    def _normalize_tex_documentclass(self, tex_code: str) -> str:
        """Force generated TEX to reference template.cls."""
        pattern = r"\\documentclass(\[[^\]]*\])?\{[^}]+\}"

        if re.search(pattern, tex_code):
            tex_code = re.sub(pattern, r"\\documentclass\1{template}", tex_code, count=1)
        else:
            tex_code = "\\documentclass{template}\n" + tex_code.lstrip()

        return self._sanitize_generated_tex(tex_code)

    def _sanitize_generated_tex(self, tex_code: str) -> str:
        """Remove high-confidence hallucinated tail blocks from generated TEX."""
        patterns = [
            r"(?is)%\s*Placeholders for figures and tables.*$",
            r"(?is)\\begin\{thebibliography\}.*?\\end\{thebibliography\}",
            r"(?im)^\s*\\bibliographystyle\{.*\}\s*$",
            r"(?im)^\s*\\bibliography\{.*\}\s*$",
            r"(?is)\\section\*?\{References\}.*$",
            r"(?is)\\section\*?\{参考文献\}.*$",
        ]

        cleaned = tex_code
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned)

        return cleaned.strip() + "\n"

    def _normalize_cls_output(self, cls_output: CLSGeneratorOutput) -> CLSGeneratorOutput:
        """Normalize escaped LaTeX sequences and keep the class name stable."""

        def normalize_value(value):
            if isinstance(value, str):
                return value.replace("\\\\", "\\")
            if isinstance(value, list):
                return [normalize_value(item) for item in value]
            if isinstance(value, dict):
                return {key: normalize_value(item) for key, item in value.items()}
            return value

        normalized = normalize_value(copy.deepcopy(cls_output.model_dump()))
        normalized["class_name"] = "template"
        return CLSGeneratorOutput.model_validate(normalized)

    async def _handle_compilation_error(
        self,
        error_log: str,
        cls_output: CLSGeneratorOutput,
        tex_output: SemanticExtractorOutput,
        style_report: StyleAnalysisReport,
        image_paths: list[str],
    ) -> tuple[CLSGeneratorOutput, SemanticExtractorOutput]:
        """辅助方法：分析错误并路由修复任务"""
        self.console.print("[yellow]🔍 正在请求 Agent 5 分析错误日志...[/yellow]")

        cls_code = build_cls_code(cls_output)
        tex_code = tex_output.tex_code
        log_snippet = error_log[-3000:] if len(error_log) > 3000 else error_log

        # 1. 诊断 (Sync Call)
        debugger_input = DebuggerInput(
            error_log=log_snippet,
            cls_snippet=cls_code[:1000],
            tex_snippet=tex_code[:1000],
        )
        debug_result: DebuggerOutput = self.debugger_agent.run(debugger_input)

        self.console.print(
            f"[bold magenta]诊断结果:[/bold magenta] {debug_result.error_summary}"
        )
        self.console.print(
            f"[dim]责任方: {debug_result.target_agent} | 建议: {debug_result.fix_instruction}[/dim]"
        )

        # 2. 路由修复 (Async Call)
        new_cls = cls_output
        new_tex = tex_output

        if debug_result.target_agent == "cls_generator":
            self.console.print("🔧 正在请求 [bold]Agent 2 (CLS)[/bold] 修复模板...")
            new_cls_input = CLSGeneratorInput(
                mode="revision",
                style_report=style_report,
                revision_feedback=f"Error: {debug_result.error_summary}\nFix: {debug_result.fix_instruction}",
                previous_config=cls_output,
            )
            new_cls = self._normalize_cls_output(
                await self.cls_agent.run_async(new_cls_input)
            )

        elif debug_result.target_agent == "semantic_extractor":
            self.console.print("🔧 正在请求 [bold]Agent 3 (TEX)[/bold] 修复正文...")
            new_tex_input = SemanticExtractorInput(
                mode="revision",
                previous_tex_code=tex_code,
                error_feedback=f"Error: {debug_result.error_summary}\nFix: {debug_result.fix_instruction}",
                images=[instructor.Image.from_path(p) for p in image_paths],
            )
            new_tex = await self.tex_agent.run_async(new_tex_input)
            new_tex = SemanticExtractorOutput(
                tex_code=self._normalize_tex_documentclass(new_tex.tex_code)
            )

        return self._normalize_cls_output(new_cls), new_tex

    # ==================================================
    # 文件操作辅助方法
    # ==================================================

    def _get_image_paths(self, base_dir: str) -> list[str]:
        """获取并验证图片路径"""
        # 这里假设使用 img_page2 作为典型页进行分析，实际可根据需求调整
        img2_path = os.path.join(base_dir, "pic", "raw", "img_page2.png")
        if not os.path.exists(img2_path):
            self.console.print(f"[bold red]错误：找不到图片文件！[/bold red]")
            self.console.print(f"请确保以下路径存在文件:\n{img2_path}")
            raise FileNotFoundError("图片文件不存在")
        return [img2_path]

    def _save_iteration_snapshot(self, attempt: int, cls_code: str, tex_code: str):
        """Persist each iteration's generated sources for inspection."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        snapshot_dir = os.path.join(project_root, "temp", "iterations")
        os.makedirs(snapshot_dir, exist_ok=True)

        cls_path = os.path.join(snapshot_dir, f"template_attempt_{attempt}.cls")
        tex_path = os.path.join(snapshot_dir, f"content_attempt_{attempt}.tex")

        with open(cls_path, "w", encoding="utf-8") as f:
            f.write(cls_code)

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_code)

    def _save_final_results(
        self, output_dir: str, cls_output, tex_output, images, is_success
    ):
        """保存所有输出文件"""
        self.console.rule("[bold cyan]保存最终结果[/bold cyan]")
        os.makedirs(output_dir, exist_ok=True)
        cls_output = self._normalize_cls_output(cls_output)

        # 保存 CLS
        cls_code = build_cls_code(cls_output)
        cls_path = os.path.join(output_dir, "template.cls")
        with open(cls_path, "w", encoding="utf-8") as f:
            f.write(cls_code)
        self.console.print(f"[green]📁 CLS 已保存: {cls_path}[/green]")

        # 保存 TEX
        tex_path = os.path.join(output_dir, "content.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_output.tex_code)
        self.console.print(f"[green]📁 TEX 已保存: {tex_path}[/green]")

        # 保存 Config (JSON)
        config_path = os.path.join(output_dir, "cls_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(cls_output.model_dump_json(indent=2))
        self.console.print(f"[dim]📁 Config 已保存: {config_path}[/dim]")

        # 保存图片
        if is_success and images:
            preview_dir = os.path.join(output_dir, "preview")
            os.makedirs(preview_dir, exist_ok=True)

            for img in images:
                p_path = os.path.join(preview_dir, img["name"])
                with open(p_path, "wb") as f:
                    f.write(base64.b64decode(img["data"]))
            self.console.print(f"[cyan]🖼️  预览图已生成: {preview_dir}[/cyan]")
        else:
            self.console.print(
                f"[yellow]虽然编译失败或未完成，但代码已保存。请手动检查 output 目录。[/yellow]"
            )

        self.console.rule("[bold green]任务结束[/bold green]")

    def _inspect_tex_code(self, tex_output)-> SemanticExtractorOutput:
        """检查TEX代码语法问题"""
        self.console.print("正在验证tex文件是否符合语法规范")
        # 准备输入
        inspect_input = TexInspectorInput(
            tex_doc=tex_output.tex_code
        )

        # 调用Tex Inspector Agent进行语法检查
        self.console.print("[cyan]Agent 6 正在检查TEX代码语法...[/cyan]")
        inspect_result = self.tex_inspector_agent.run(inspect_input)

        # 将检查结果转换为SemanticExtractorOutput类型，保持与现有工作流的兼容性
        refined_tex_output = SemanticExtractorOutput(
            tex_code=inspect_result.tex_doc_after
        )

        self.console.print("[green]✅ TEX代码语法检查完成！[/green]")
        return refined_tex_output

    def _inspect_cls_code(self, cls_output):
        """检查CLS代码语法问题"""
        self.console.print("正在验证cls文件是否符合语法规范")
        # 准备输入
        inspect_input = CLSInspectorInput(
            cls_doc=build_cls_code(cls_output)
        )

        self.console.print("[cyan]Agent 7 正在检查CLS代码语法...[/cyan]")
        inspect_result = self.cls_inspector_agent.run(inspect_input)
        refined_cls_output = CLSGeneratorOutput(
            class_name=cls_output.class_name,
            base_class=cls_output.base_class,
            is_twocolumn=cls_output.is_twocolumn,
            geometry=cls_output.geometry,
            fonts=cls_output.fonts,
            title=cls_output.title,
            author=cls_output.author,
            abstract=cls_output.abstract,
            sections=cls_output.sections,
            header_footer=cls_output.header_footer,
            paragraph=cls_output.paragraph,
            caption=cls_output.caption,
            additional_packages=cls_output.additional_packages,
            custom_commands=inspect_result.cls_doc_after
        )
        self.console.print("[green]✅ CLS代码语法检查完成！[/green]")
        return refined_cls_output

    # async def _async_inspect_tex_code(self, tex_output) -> SemanticExtractorOutput:
    #     """检查TEX代码语法问题（异步版）"""
    #
    #     def sync_inspect():
    #         return self._inspect_tex_code(tex_output)
    #
    #     # 使用run_in_executor将同步方法转换为异步执行
    #     loop = asyncio.get_event_loop()
    #     return await loop.run_in_executor(None, sync_inspect)
    #
    # async def _async_inspect_cls_code(self, cls_output):
    #     """检查CLS代码语法问题（异步版）"""
    #
    #     def sync_inspect():
    #         return self._inspect_cls_code(cls_output)
    #
    #     # 使用run_in_executor将同步方法转换为异步执行
    #     loop = asyncio.get_event_loop()
    #     return await loop.run_in_executor(None, sync_inspect)

    def _inspect_combined_code(self, tex_output, cls_output):
        """同时检查TEX和CLS代码语法问题"""

        # 准备输入
        tex_doc = tex_output.tex_code
        cls_doc = build_cls_code(cls_output)

        inspect_input = CombinedInspectorInput(
            tex_doc=tex_doc,
            cls_doc=cls_doc
        )

        # 调用Combined Inspector Agent进行语法检查
        self.console.print("[cyan]Agent 8 正在同时检查TEX和CLS代码语法...[/cyan]")
        inspect_result = self.combined_inspector_agent.run(inspect_input)

        # 将检查结果转换为相应类型，保持与现有工作流的兼容性
        refined_tex_output = SemanticExtractorOutput(
            tex_code=inspect_result.tex_doc_after
        )

        # 重构CLSGeneratorOutput，这里需要根据实际的CLS结构解析返回的内容
        refined_cls_output = CLSGeneratorOutput(
            class_name=cls_output.class_name,
            base_class=cls_output.base_class,
            is_twocolumn=cls_output.is_twocolumn,
            geometry=cls_output.geometry,
            fonts=cls_output.fonts,
            title=cls_output.title,
            author=cls_output.author,
            abstract=cls_output.abstract,
            sections=cls_output.sections,
            header_footer=cls_output.header_footer,
            paragraph=cls_output.paragraph,
            caption=cls_output.caption,
            additional_packages=cls_output.additional_packages,
            custom_commands=inspect_result.cls_doc_after  # 假设custom_commands字段存储.cls内容
        )

        self.console.print("[green]✅ TEX和CLS代码语法检查完成！[/green]")
        return refined_tex_output, refined_cls_output

    async def _async_inspect_combined_code(self, tex_output, cls_output):
        """合并检查TEX和CLS代码语法问题（异步版）"""

        def sync_inspect():
            return self._inspect_combined_code(tex_output, cls_output)

        # 使用run_in_executor将同步方法转换为异步执行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_inspect)

    def _generate_initial_code_new(self, image_paths: List[str]):
        """阶段一&二：使用图像识别器分析视觉样式并生成初始代码 (同步调用)"""
        self.console.rule("[bold cyan]阶段一&二：图像识别与代码生成[/bold cyan]")
        
        # 准备输入 - 使用图像识别器同时生成 CLS 和 TEX
        img_recognizer_input = ImgRecognizerInput(
            instruction_text=(
                "请分析这些论文截图的全局布局、页眉页脚、字体特征，并提取文本内容生成对应的 .cls 和 .tex 文件。\n\n"
                "【样式分析】分析页面布局、分栏、页眉页脚、字体特征等。\n"
                "【TEX 生成】从截图中提取文本内容，生成 .tex 文件，图片/表格用占位符替代。\n"
                "【CLS 生成】根据样式特征生成 .cls 模板文件。\n\n"
                "【禁止】在 TEX 文件中使用 \\textbf, \\Large, \\vspace 等样式命令。"
            ),
            images=[instructor.Image.from_path(p) for p in image_paths],
        )

        self.console.print("[yellow]🚀 正在生成初始代码...[/yellow]")
        
        # 调用图像识别器 Agent 并发生成 CLS 和 TEX 代码
        recognition_result = self.img_recognizer_agent.run(img_recognizer_input)
        
        # 为了兼容现有工作流程，我们需要解析生成的 cls 代码并构建一个合适的 CLSGeneratorOutput 对象
        # 由于 agent9 直接生成完整的 cls 代码，我们将使用解析出的信息填充 CLSGeneratorOutput 结构
        
        # 从生成的 cls 代码中提取关键信息
        is_twocolumn = "twocolumn" in recognition_result.cls_code.lower()
        has_geometry = "geometry" in recognition_result.cls_code.lower()
        
        # 构建 CLSGeneratorOutput 对象
        # 使用解析出的信息构建尽可能准确的结构化配置
        cls_output = CLSGeneratorOutput(
            class_name="template",
            base_class="article",
            is_twocolumn=is_twocolumn,
            geometry=GeometrySettings(
                top_margin="25mm" if not has_geometry else "25mm",  # 默认值，实际布局在 custom_commands 中
                bottom_margin="25mm",
                left_margin="25mm",
                right_margin="25mm",
                column_sep="10mm" if is_twocolumn else None,
            ),
            fonts=FontSettings(
                base_font_size="10pt",
                main_font_family="serif",
                math_font_package="newtxmath",
                use_microtype=True,
            ),
            title=TitleSettings(
                font_size="\\large",
                font_weight="bold",
                font_family="serif",
                alignment="center",
                space_before="0pt",
                space_after="18pt",
            ),
            author=AuthorSettings(
                name_font_size="\\normalsize",
                name_font_weight="normal",
                affiliation_font_size="\\small",
                affiliation_font_style="italic",
                alignment="center",
                space_after="18pt",
            ),
            abstract=AbstractSettings(
                font_size="\\small",
                font_style="normal",
                left_indent="0pt",
                right_indent="0pt",
                heading_text="Abstract",
                heading_font_weight="bold",
                space_before="12pt",
                space_after="24pt",
            ),
            sections=SectionSettings(
                section_font_size="\\large",
                section_font_weight="bold",
                section_font_family="serif",
                section_alignment="left",
                section_numbering_format="arabic",
                section_space_before="12pt",
                section_space_after="6pt",
                subsection_font_size="\\normalsize",
                subsection_font_weight="bold",
                subsection_font_style="normal",
                subsection_space_before="12pt",
                subsection_space_after="6pt",
            ),
            header_footer=HeaderFooterSettings(
                first_page_header_left="",
                first_page_header_center="",
                first_page_header_right="",
                first_page_footer_center="\\thepage",
                first_page_has_rule=False,
                running_header_left="",
                running_header_center="",
                running_header_right="\\thepage",
                running_footer_center="",
                header_rule_width="0.4pt",
                footer_rule_width="0pt",
            ),
            paragraph=ParagraphSettings(
                line_spread="1.0",
                paragraph_indent="2em",
                paragraph_skip="0pt",
                text_justification="justified",
            ),
            caption=CaptionSettings(
                font_size="\\small",
                label_font_weight="bold",
                label_separator=":",
                figure_position="below",
                table_position="above",
            ),
            additional_packages=[],
            custom_commands=recognition_result.cls_code,  # 将 agent9 生成的完整 cls 代码放入 custom_commands
        )
        
        # 构造 TEX 输出
        tex_output = SemanticExtractorOutput(
            tex_code=self._normalize_tex_documentclass(recognition_result.tex_code)
        )
        
        self.console.print("[green]✅ 初始代码生成完成！[/green]")
        return cls_output, tex_output

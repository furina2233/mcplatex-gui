import asyncio

import instructor

from agents.cls_generator import CLSGeneratorInput, CLSGeneratorOutput
from agents.semantic_extractor import SemanticExtractorInput, SemanticExtractorOutput
from agents.style_analyzer import StyleAnalysisInput, StyleAnalysisReport
from services.workflow_support import (
    HEADER_FOOTER_RESTORATION_GUIDANCE,
    normalize_cls_output,
    normalize_tex_documentclass,
)


class GenerationService:
    def __init__(self, style_agent, cls_agent, tex_agent, console):
        self.style_agent = style_agent
        self.cls_agent = cls_agent
        self.tex_agent = tex_agent
        self.console = console

    def analyze_style(self, image_paths: list[str]) -> StyleAnalysisReport:
        style_input = StyleAnalysisInput(
            instruction_text=(
                "Analyze the provided paper screenshots and estimate structured layout parameters. "
                "You must identify margins, column count, column gap, header height, header-to-text spacing, "
                "footer spacing, paragraph indent, body line spacing, paragraph spacing, section and subsection "
                "spacing, title/author/abstract spacing, caption spacing, and representative font/alignment features. "
                f"{HEADER_FOOTER_RESTORATION_GUIDANCE}"
            ),
            images=[instructor.Image.from_path(path) for path in image_paths],
        )
        return self.style_agent.run(style_input)

    async def generate(self, image_paths: list[str]) -> tuple[StyleAnalysisReport, CLSGeneratorOutput, SemanticExtractorOutput]:
        self.console.rule("[bold cyan]阶段一：识别并生成 TEX/CLS[/bold cyan]")
        style_report = await asyncio.to_thread(self.analyze_style, image_paths)

        cls_input = CLSGeneratorInput(
            mode="initial",
            style_report=style_report,
        )
        tex_input = SemanticExtractorInput(
            mode="initial",
            instruction_text=(
                "Please extract only the clearly visible paper text into a clean LaTeX document. "
                "Do not invent missing content. Figures and tables must remain placeholders with captions only. "
                f"{HEADER_FOOTER_RESTORATION_GUIDANCE}"
            ),
            images=[instructor.Image.from_path(path) for path in image_paths],
        )

        cls_output, tex_output = await asyncio.gather(
            self.cls_agent.run_async(cls_input),
            self.tex_agent.run_async(tex_input),
        )

        normalized_cls = normalize_cls_output(cls_output)
        normalized_tex = SemanticExtractorOutput(
            tex_code=normalize_tex_documentclass(tex_output.tex_code)
        )
        return style_report, normalized_cls, normalized_tex

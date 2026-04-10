import asyncio

import instructor

from agents.cls_generator import CLSGeneratorInput, CLSGeneratorOutput
from agents.visual_auditor import VisualAuditorInput, VisualAuditorOutput
from schemas.style_schema import StyleAnalysisReport
from services.workflow_support import (
    HEADER_FOOTER_AUDIT_GUIDANCE,
    HEADER_FOOTER_REVISION_GUIDANCE,
    normalize_cls_output,
)


class OptimizationService:
    def __init__(self, visual_auditor_agent, cls_agent, console):
        self.visual_auditor_agent = visual_auditor_agent
        self.cls_agent = cls_agent
        self.console = console

    def audit(self, original_path: str, rendered_image: dict[str, str], cls_output: CLSGeneratorOutput) -> VisualAuditorOutput:
        audit_input = VisualAuditorInput(
            images=[
                instructor.Image.from_path(original_path),
                instructor.Image.from_path(rendered_image["path"]),
            ],
            instruction_text=(
                "Compare the original paper screenshot with the rendered PDF page. "
                "Focus only on layout, margins, header/footer placement, spacing, fonts, title/abstract/section block geometry, "
                "and whether the rendered page contains hallucinated trailing content not present in the original image. "
                "Ignore OCR wording mistakes. "
                f"{HEADER_FOOTER_AUDIT_GUIDANCE} "
                "Return only field-level feedback that maps to the CLS generator schema.\n\n"
                f"Current CLS configuration:\n{cls_output.model_dump_json(indent=2)}"
            ),
        )
        return self.visual_auditor_agent.run(audit_input)

    async def optimize(
        self,
        style_report: StyleAnalysisReport,
        cls_output: CLSGeneratorOutput,
        original_path: str,
        rendered_image: dict[str, str],
    ) -> tuple[CLSGeneratorOutput, VisualAuditorOutput]:
        audit_result = await asyncio.to_thread(self.audit, original_path, rendered_image, cls_output)
        if audit_result.passed:
            return cls_output, audit_result

        new_cls_input = CLSGeneratorInput(
            mode="revision",
            style_report=style_report,
            revision_feedback=(
                "Render Comparison Audit Failed. "
                f"{HEADER_FOOTER_REVISION_GUIDANCE} "
                f"Feedback: {audit_result.feedback}"
            ),
            previous_config=cls_output,
        )
        revised_cls = await self.cls_agent.run_async(new_cls_input)
        return normalize_cls_output(revised_cls), audit_result

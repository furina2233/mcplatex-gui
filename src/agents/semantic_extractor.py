# agents/semantic_extractor.py
import instructor
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import ChatHistory
from agent_setup import semantic_extractor_config
from typing import List, Literal, Optional


class SemanticExtractorOutput(BaseIOSchema):
    """
    语义内容提取员 (Semantic Extractor) 的输出。
    """

    tex_code: str = Field(
        ...,
        description=(
            "完整的 LaTeX .tex 文件源代码。\n\n"
            "【文件结构】\n"
            "\\documentclass{template}\n"
            "\\begin{document}\n"
            "\\title{...}\n"
            "\\author{...}\n"
            "\\maketitle\n"
            "\\begin{abstract}...\\end{abstract}\n"
            "\\section{...}\n"
            "...\n"
            "\\end{document}\n\n"
            "【图片占位符 - 替代所有图片，忽略图片内部所有内容】\n"
            "\\begin{figure}[htbp]\n"
            "\\centering\n"
            "\\fbox{\\parbox{0.8\\linewidth}{\\centering\\vspace{3cm}[FIGURE PLACEHOLDER]\\vspace{3cm}}}\n"
            "\\caption{图片的原始标题}\n"
            "\\end{figure}\n\n"
            "【表格占位符 - 替代所有表格，忽略表格内部所有内容】\n"
            "\\begin{table}[htbp]\n"
            "\\centering\n"
            "\\caption{表格的原始标题}\n"
            "\\fbox{\\parbox{0.9\\linewidth}{\\centering\\vspace{2cm}[TABLE PLACEHOLDER]\\vspace{2cm}}}\n"
            "\\end{table}\n\n"
            "【禁止】\n"
            "- 提取图片/表格内部的任何内容\n"
            "- 使用 \\textbf, \\textit, \\Large, \\vspace, \\\\ 等样式命令"
        ),
    )


# =============================================================================
# 输入 Schema
# =============================================================================
class SemanticExtractorInput(BaseIOSchema):
    """
    语义内容提取员的输入。
    支持 'initial' (从图提取) 和 'revision' (根据错误修复) 两种模式。
    """

    mode: Literal["initial", "revision"] = Field(
        default="initial",
        description="工作模式：'initial' 为从图片提取，'revision' 为根据错误修复代码。",
    )

    # Initial 模式主要参数
    instruction_text: Optional[str] = Field(
        default=None, description="初始提取的具体指令。在 mode='initial' 时必填。"
    )

    images: Optional[List[instructor.Image]] = Field(
        default=None, description="PDF 页面截图。在 mode='initial' 时必填。"
    )

    # Revision 模式主要参数
    previous_tex_code: Optional[str] = Field(
        default=None,
        description="上一次生成的导致报错的 .tex 代码。在 mode='revision' 时必填。",
    )

    error_feedback: Optional[str] = Field(
        default=None,
        description="编译器报错信息或 Debugger 的修复建议。在 mode='revision' 时必填。",
    )


def create_semantic_extractor_agent(
    client, model: str, history: ChatHistory | None = None
) -> AtomicAgent:
    """
    创建并配置 Agent 3: 语义内容提取员
    输入：SemanticExtractorInput (包含图片)
    输出：ContentExtractorOutput
    """

    if history is None:
        history = ChatHistory()

    agent = AtomicAgent[SemanticExtractorInput, SemanticExtractorOutput](
        config=AgentConfig(
            client=client,
            model=model,
            model_api_parameters={
                "max_tokens": 131072,
                "max_retries": 3,
                "temperature": 0.1,
            },
            system_prompt_generator=semantic_extractor_config.system_prompt_generator,
            history=history,
        )
    )

    return agent

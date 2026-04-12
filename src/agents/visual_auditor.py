# agents/visual_auditor.py
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig
from atomic_agents.context import ChatHistory
from agent_setup import visual_auditor_config
from atomic_agents import BaseIOSchema
import instructor


class VisualAuditorInput(BaseIOSchema):
    """
    视觉审计员的输入数据结构。
    包含原版截图和生成版截图，用于像素级对比。
    """

    images: list[instructor.Image] = Field(
        ...,
        description="包含两张图片的列表：[图1: 原版PDF截图, 图2: 复刻版预览截图]。顺序必须严格遵守。",
    )

    instruction_text: str = Field(
        default="请对比这两张图片。图1是原版，图2是当前复刻版。请忽略文字内容的拼写错误（如OCR误差），专注于排版、布局、字体、间距等视觉样式的差异。",
        description="给 Agent 的具体指令上下文",
    )


class VisualAuditorOutput(BaseIOSchema):
    """
    视觉审计员的输出报告。
    """

    passed: bool = Field(
        ...,
        description="如果视觉样式（字体、边距、间距）与原版高度一致（允许微小误差），则为 True。如果存在明显的布局或排版缺陷，则为 False。",
    )

    feedback: str = Field(
        ...,
        description=(
            "如果 passed 为 False，请提供针对 .cls 文件的修改建议列表。\n"
            "格式要求：[类别]: 具体问题 + 具体参数调整建议。\n"
            "类别包括：[Geometry], [Font], [Spacing], [Header], [Title].\n"
            "例如：'[Spacing]: 段间距过大，建议减少 \\parskip'。\n"
            "如果 passed 为 True，必须输出字符串 '验收通过'。"
        ),
    )


def create_visual_auditor_agent(
    client, model: str, history: ChatHistory | None = None
) -> AtomicAgent:
    """
    创建并配置 Agent 4: 视觉差异审计员
    输入：VisualAuditorInput
    输出：VisualAuditorOutput
    """

    if history is None:
        history = ChatHistory()

    agent = AtomicAgent[VisualAuditorInput, VisualAuditorOutput](
        config=AgentConfig(
            client=client,
            model=model,
            model_api_parameters={
                "max_tokens": 65536,
                "temperature": 0.1,
            },
            system_prompt_generator=visual_auditor_config.system_prompt_generator,
            history=history,
        )
    )

    return agent

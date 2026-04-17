# src/agents/manual_adjustor.py
"""手动调整Agent：根据用户反馈修改LaTeX模板配置"""

import json

from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import ChatHistory, SystemPromptGenerator
from pydantic import Field

from llm_client import TEXT_MODEL, text_client
from schemas.cls_schema import CLSGeneratorOutput


class ManualAdjustorInput(BaseIOSchema):
    """手动调整Agent的输入"""

    user_feedback: str = Field(
        ...,
        description="用户对模板的修改反馈，例如：标题字体偏小、页边距需要增大等",
    )
    cls_config: str = Field(
        ...,
        description="当前模板的完整CLS配置对象（JSON格式），包含所有属性的当前值",
    )
    tex_code: str = Field(
        ...,
        description="当前的LaTeX .tex 文档代码",
    )


class CLSFieldModification(BaseIOSchema):
    """单个字段的修改"""

    field_path: str = Field(
        ...,
        description="要修改的字段路径，使用点号分隔，如 'title.font_size', 'geometry.top_margin', 'sections.section_font_size'",
    )
    new_value: str | int | float | bool | list | dict | None = Field(
        ...,
        description="该字段的新值，必须与原字段类型兼容",
    )


class ManualAdjustorOutput(BaseIOSchema):
    """手动调整Agent的输出"""

    modifications: list[CLSFieldModification] = Field(
        ...,
        description="需要修改的字段列表，只包含与用户反馈相关的字段",
    )
    tex_code_after: str = Field(
        ...,
        description="根据用户反馈修改后的 .tex 代码（如果不需要修改.tex，返回原代码）",
    )
    explanation: str = Field(
        default="",
        description="对修改内容的简要说明",
    )


def _build_system_prompt() -> SystemPromptGenerator:
    """构建系统提示词"""

    # 获取 CLSGeneratorOutput 的完整 Schema
    cls_schema = CLSGeneratorOutput.model_json_schema()

    return SystemPromptGenerator(
        background=[
            "你是一个LaTeX模板配置专家，擅长根据用户的自然语言反馈修改模板配置。",
            f"模板配置是一个结构化的JSON对象，符合以下JSON Schema:\n{json.dumps(cls_schema, indent=2, ensure_ascii=False)}",
        ],
        steps=[
            "1. 仔细阅读用户的修改反馈",
            "2. 分析当前的CLS配置JSON，理解每个属性的含义和当前值",
            "3. 确定哪些配置字段与用户的修改要求相关",
            "4. 对于每个相关字段，计算出合适的新值",
            "5. 如果需要修改.tex代码（如标题、作者等内容），返回修改后的完整.tex代码",
            "6. 返回修改列表和修改说明",
        ],
        output_instructions=[
            "【重要】只修改与用户反馈直接相关的字段！对于无关字段，绝对不要包含在modifications列表中",
            "field_path 必须使用点号分隔的路径格式，如 'title.font_size', 'geometry.top_margin'",
            "新值必须与原字段类型兼容，不能改变字段类型",
            "如果需要修改嵌套对象的属性，使用完整路径，如 'header_footer.journal_header_lines'",
            "modifications列表应该尽可能精简，只包含真正需要修改的字段",
            "如果用户的反馈只涉及.cls配置，tex_code_after 应该返回原始的.tex代码",
            "如果用户的反馈涉及.tex内容（如标题文字），才修改tex_code_after",
            "explanation 应该简明扼要地说明做了什么修改，用中文",
        ],
    )


def create_manual_adjustor_agent(
        client=None, model: str = TEXT_MODEL, history: ChatHistory | None = None
) -> AtomicAgent:
    """
    创建并配置手动调整Agent
    使用文本模型，根据用户反馈修改LaTeX模板配置
    """

    if history is None:
        history = ChatHistory()

    system_prompt = _build_system_prompt()

    client_to_use = client or text_client

    agent = AtomicAgent[ManualAdjustorInput, ManualAdjustorOutput](
        config=AgentConfig(
            client=client_to_use,
            model=model,
            model_api_parameters={
                "max_tokens": 65536,
                "max_retries": 3,
                "temperature": 0.2,
            },
            system_prompt_generator=system_prompt,
            history=history,
        )
    )

    return agent

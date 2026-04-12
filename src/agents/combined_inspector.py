# src/agents/combined_inspector.py
# agents/combined_inspector.py
import instructor
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import ChatHistory
from agent_setup import combined_inspector_config
from typing import List, Optional


class CombinedInspectorOutput(BaseIOSchema):
    """
    LaTeX TEX和CLS代码语法检查专家的输出。
    包含修复后的TEX和CLS代码。
    """

    tex_doc_after: str = Field(
        ...,
        description="修复后的 LaTeX (.tex) 代码。",
    )

    cls_doc_after: str = Field(
        ...,
        description="修复后的 LaTeX (.cls) 代码。",
    )


class CombinedInspectorInput(BaseIOSchema):
    """
    LaTeX TEX和CLS代码语法检查专家的输入。
    包含当前的 .tex 和 .cls 代码。
    """

    tex_doc: str = Field(
        ...,
        description="当前的 LaTeX (.tex) 代码。",
    )

    cls_doc: str = Field(
        ...,
        description="当前的 LaTeX (.cls) 代码。",
    )


def create_combined_inspector_agent(
        client, model: str, history: ChatHistory | None = None
) -> AtomicAgent:
    """
    创建并配置 TEX和CLS 代码语法检查专家
    输入：CombinedInspectorInput (包含 .tex 和 .cls 代码)
    输出：CombinedInspectorOutput (修复后的.tex和.cls代码)
    """

    if history is None:
        history = ChatHistory()

    agent = AtomicAgent[CombinedInspectorInput, CombinedInspectorOutput](
        config=AgentConfig(
            client=client,
            model=model,
            model_api_parameters={
                "max_tokens": 65536,
                "max_retries": 3,
                "temperature": 0.1,
            },
            system_prompt_generator=combined_inspector_config.system_prompt_generator,
            history=history,
        )
    )

    return agent
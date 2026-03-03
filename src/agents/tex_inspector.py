# agents/tex_accuracy_verifier.py
import instructor
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import ChatHistory
from agent_setup import tex_inspector_config
from typing import List, Optional


class TexInspectorOutput(BaseIOSchema):
    """
    LaTeX 文本准确度验证专家的输出。
    包含语法问题修复建议和内容准确度修复建议。
    """

    tex_doc_after: str = Field(
        ...,
        description="修复后的 LaTeX (.tex) 代码。",
    )


class TexInspectorInput(BaseIOSchema):
    """
    LaTeX 文本准确度验证专家的输入。
    包含前的 .tex 代码。
    """

    tex_doc: str = Field(
        ...,
        description="当前的 LaTeX (.tex) 代码。",
    )



def create_tex_inspector_agent(
    client, model: str, history: ChatHistory | None = None
) -> AtomicAgent:
    """
    创建并配置 Agent 6: LaTeX 文本准确度验证专家
    输入：TexInspectorInput (包含 .tex 代码)
    输出：TexInspectorOutput (结构化的验证报告)
    """

    if history is None:
        history = ChatHistory()

    agent = AtomicAgent[TexInspectorInput, TexInspectorOutput](
        config=AgentConfig(
            client=client,
            model=model,
            model_api_parameters={
                "max_tokens": 8192,  # 增加输出上限，防止 JSON 被截断
                "max_retries": 3,
                "temperature": 0.1,  # 降低随机性，有助于格式稳定
            },
            system_prompt_generator=tex_inspector_config.system_prompt_generator,
            history=history,
        )
    )

    return agent
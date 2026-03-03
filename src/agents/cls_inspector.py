# agents/cls_inspector.py
import instructor
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import ChatHistory
from agent_setup import cls_inspector_config
from typing import List, Optional


class CLSInspectorOutput(BaseIOSchema):
    """
    LaTeX 文档类文件(.cls)语法检查专家的输出。
    包含修复后的.cls代码。
    """

    cls_doc_after: str = Field(
        ...,
        description="修复后的 LaTeX (.cls) 代码。",
    )


class CLSInspectorInput(BaseIOSchema):
    """
    LaTeX 文档类文件(.cls)语法检查专家的输入。
    包含当前的 .cls 代码。
    """

    cls_doc: str = Field(
        ...,
        description="当前的 LaTeX (.cls) 代码。",
    )


def create_cls_inspector_agent(
        client, model: str, history: ChatHistory | None = None
) -> AtomicAgent:
    """
    创建并配置 CLS 文件语法检验专家
    输入：CLSInspectorInput (包含 .cls 代码)
    输出：CLSInspectorOutput (修复后的.cls代码)
    """

    if history is None:
        history = ChatHistory()

    agent = AtomicAgent[CLSInspectorInput, CLSInspectorOutput](
        config=AgentConfig(
            client=client,
            model=model,
            model_api_parameters={
                "max_tokens": 8192,  # 增加输出上限，防止 JSON 被截断
                "max_retries": 3,
                "temperature": 0.1,  # 降低随机性，有助于格式稳定
            },
            system_prompt_generator=cls_inspector_config.system_prompt_generator,
            history=history,
        )
    )

    return agent
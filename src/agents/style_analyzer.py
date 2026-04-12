# agents/style_analyzer.py
import instructor
from typing import List
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import ChatHistory
from agent_setup import style_analyzer_config
from schemas.style_schema import StyleAnalysisReport


# =============================================================================
# 自定义输入 Schema，支持多张图片
# =============================================================================
class StyleAnalysisInput(BaseIOSchema):
    """
    样式分析师的输入载体。
    包含文本指令和多张待分析的论文截图。
    """

    instruction_text: str = Field(
        ..., description="给分析师的具体指令，例如'请分析这张图的latex样式'。"
    )
    images: List[instructor.Image] = Field(
        ..., description="论文截图列表。通常包含：[图1:首页, 图2:内页]。"
    )


def create_style_analyzer_agent(
    client, model: str, history: ChatHistory | None = None
) -> AtomicAgent:
    """
    创建并配置 Agent 1: 样式分析师
    输入：StyleAnalysisInput (包含图片)
    输出：StyleAnalysisReport (结构化报告)
    """

    # 1. 初始化 Memory
    if history is None:
        history = ChatHistory()

    # 2. 创建 Agent
    agent = AtomicAgent[StyleAnalysisInput, StyleAnalysisReport](
        config=AgentConfig(
            client=client,
            model=model,
            model_api_parameters={
                "max_tokens": 65536,
                "max_retries": 3,
                "temperature": 0.1,
            },
            system_prompt_generator=style_analyzer_config.system_prompt_generator,
            history=history,
        )
    )

    return agent

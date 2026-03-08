from typing import List

import instructor
from atomic_agents import BaseIOSchema, AtomicAgent, AgentConfig
from atomic_agents.context import ChatHistory
from pydantic import Field

from agent_setup import combined_inspector_config


class ImgRecognizerOutput(BaseIOSchema):
    """
        图像识别器的输出，包含生成的 LaTeX 代码。
        """
    tex_code: str = Field(
        ...,
        description="LaTeX (.tex) 代码。",
    )
    cls_code: str = Field(
        ...,
        description="LaTeX (.cls) 代码。",
    )
class ImgRecognizerInput(BaseIOSchema):
    """
       图像识别器的输入，包含待分析的图片和指令。
    """
    instruction_text: str = Field(
        ..., description="给分析师的具体指令，例如'请分析这张图的latex样式'。"
    )
    images: List[instructor.Image] = Field(
        ..., description="论文截图列表。通常包含：[图1:首页, 图2:内页]。"
    )
def create_img_recognizer_agent(
    client, model: str, history: ChatHistory | None = None
) -> AtomicAgent:
    """
    创建并配置 Agent 1: 图片识别器
    输入：ImgRecognizerInput (包含图片)
    输出：ImgRecognizerOutput (结构化报告)
    """

    # 1. 初始化 Memory
    if history is None:
        history = ChatHistory()

    # 2. 创建 Agent
    agent = AtomicAgent[ImgRecognizerInput, ImgRecognizerOutput](
        config=AgentConfig(
            client=client,
            model=model,
            model_api_parameters={
                "max_tokens": 65536,  # 增加输出上限，防止 JSON 被截断
                "max_retries": 3,
                "temperature": 0.1,  # 降低随机性，有助于格式稳定
            },
            system_prompt_generator=combined_inspector_config.system_prompt_generator,
            history=history,
        )
    )

    return agent
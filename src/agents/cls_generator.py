# agents/cls_generator.py
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import ChatHistory
from agent_setup import cls_generator_config
from schemas.cls_schema import CLSGeneratorOutput
from schemas.style_schema import StyleAnalysisReport


# =============================================================================
# 输入 Schema
# =============================================================================
class CLSGeneratorInput(BaseIOSchema):
    """
    模板架构师的输入载体。
    """

    mode: str = Field(
        ...,
        description="输入模式：'initial' 表示初次生成，'revision' 表示迭代修正。",
    )
    style_report: StyleAnalysisReport | None = Field(
        default=None,
        description="样式分析报告（初次生成时必须提供）。",
    )
    revision_feedback: str | None = Field(
        default=None,
        description="差异修正报告或编译错误信息（迭代修正时提供）。",
    )
    previous_config: CLSGeneratorOutput | None = Field(
        default=None,
        description="上一版本的配置（迭代修正时提供，便于参考和增量修改）。",
    )


def create_cls_generator_agent(
    client, model: str, history: ChatHistory | None = None
) -> AtomicAgent:
    """
    创建并配置 Agent 2: 模板架构师
    输入：CLSGeneratorInput
    输出：CLSGeneratorOutput (结构化配置)
    """

    if history is None:
        history = ChatHistory()

    agent = AtomicAgent[CLSGeneratorInput, CLSGeneratorOutput](
        config=AgentConfig(
            client=client,
            model=model,
            model_api_parameters={
                "max_tokens": 8192,
                "max_retries": 3,
                "temperature": 0.2,
            },
            system_prompt_generator=cls_generator_config.system_prompt_generator,
            history=history,
        )
    )

    return agent

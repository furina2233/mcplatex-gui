# agents/debugger_agent.py
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig
from atomic_agents.context import ChatHistory
from agent_setup import compiler_debugger_config
from typing import Literal
from atomic_agents import BaseIOSchema


class DebuggerInput(BaseIOSchema):
    """
    编译错误调试器的输入数据结构。
    包含编译日志和相关的代码片段，用于分析错误原因。
    """

    error_log: str = Field(..., description="LaTeX 编译器的错误日志")
    cls_snippet: str = Field(..., description="CLS 文件的前几行（用于判断文档类）")
    tex_snippet: str = Field(..., description="TEX 文件的前几行")


class DebuggerOutput(BaseIOSchema):
    """
    编译错误诊断专家的输出。
    决定下一步是修复 CLS 还是修复 TEX。
    """

    error_summary: str = Field(
        ...,
        description="用简练而准确的语言总结编译错误的原因。例如：'正文中出现了未转义的 % 符号' 或 'geometry 宏包参数设置冲突'。",
    )

    target_agent: Literal["cls_generator", "semantic_extractor"] = Field(
        ...,
        description=(
            "指定哪个 Agent 需要进行修复。\n"
            "- 'cls_generator': 如果错误与宏包、文档类选项、Preamble 定义有关。\n"
            "- 'semantic_extractor': 如果错误与正文内容、特殊字符转义、数学公式语法有关。"
        ),
    )

    fix_instruction: str = Field(
        ...,
        description="给目标 Agent 的具体修复指令。例如：'请找到正文中的 % 符号并将其替换为 \\%'。",
    )


def create_debugger_agent(
    client, model: str, history: ChatHistory | None = None
) -> AtomicAgent:
    """
    创建并配置 Agent 5: LaTeX 编译日志分析专家
    输入：DebuggerInput
    输出：DebuggerOutput (结构化配置)
    """

    if history is None:
        history = ChatHistory()

    agent = AtomicAgent[DebuggerInput, DebuggerOutput](
        config=AgentConfig(
            client=client,
            model=model,
            model_api_parameters={
                "max_tokens": 65536,
                "max_retries": 3,
                "temperature": 0.2,
            },
            system_prompt_generator=compiler_debugger_config.system_prompt_generator,
            history=history,
        )
    )

    return agent

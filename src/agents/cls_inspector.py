from atomic_agents import AgentConfig, AtomicAgent, BaseIOSchema
from atomic_agents.context import ChatHistory
from pydantic import Field

from agent_setup import cls_inspector_config


class CLSInspectorOutput(BaseIOSchema):
    """Full CLS document after minimal repair."""

    cls_doc_after: str = Field(..., description="The repaired LaTeX .cls document.")


class CLSInspectorInput(BaseIOSchema):
    """Current CLS document plus optional compiler feedback."""

    cls_doc: str = Field(..., description="The current LaTeX .cls document.")
    error_feedback: str | None = Field(
        default=None,
        description="Optional compiler error summary and fix instruction for targeted repair.",
    )


def create_cls_inspector_agent(
    client, model: str, history: ChatHistory | None = None
) -> AtomicAgent:
    if history is None:
        history = ChatHistory()

    agent = AtomicAgent[CLSInspectorInput, CLSInspectorOutput](
        config=AgentConfig(
            client=client,
            model=model,
            model_api_parameters={
                "max_tokens": 65536,
                "max_retries": 3,
                "temperature": 0.1,
            },
            system_prompt_generator=cls_inspector_config.system_prompt_generator,
            history=history,
        )
    )

    return agent

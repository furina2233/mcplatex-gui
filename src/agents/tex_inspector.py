from atomic_agents import AgentConfig, AtomicAgent, BaseIOSchema
from atomic_agents.context import ChatHistory
from pydantic import Field

from agent_setup import tex_inspector_config


class TexInspectorOutput(BaseIOSchema):
    """Full TEX document after minimal repair."""

    tex_doc_after: str = Field(..., description="The repaired LaTeX .tex document.")


class TexInspectorInput(BaseIOSchema):
    """Current TEX document plus optional compiler feedback."""

    tex_doc: str = Field(..., description="The current LaTeX .tex document.")
    error_feedback: str | None = Field(
        default=None,
        description="Optional compiler error summary and fix instruction for targeted repair.",
    )


def create_tex_inspector_agent(
        client, model: str, history: ChatHistory | None = None
) -> AtomicAgent:
    if history is None:
        history = ChatHistory()

    agent = AtomicAgent[TexInspectorInput, TexInspectorOutput](
        config=AgentConfig(
            client=client,
            model=model,
            model_api_parameters={
                "max_tokens": 65536,
                "max_retries": 3,
                "temperature": 0.1,
            },
            system_prompt_generator=tex_inspector_config.system_prompt_generator,
            history=history,
        )
    )

    return agent

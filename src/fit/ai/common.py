from pydantic_ai import Agent
from pydantic import BaseModel
from typing import Type

STRUCTURED_MODELS = ["gpt-4.1"]
DEFAULT_LARGE_MODEL = "gpt-4.1"
DEFAULT_SMALL_MODEL = "gpt-5-mini"


def natural_language_agent(
    model: str, system: str, output_type: Type[BaseModel] | None = None
) -> Agent:
    if output_type is not None:
        return Agent(f"openai:{model}", system_prompt=system, output_type=output_type)
    else:
        return Agent(f"openai:{model}", system_prompt=system)

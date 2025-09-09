from pydantic_ai import Agent
from pydantic import BaseModel
from typing import Type

STRUCTURED_MODELS = ["gpt-4o-2024-08-06"]
DEFAULT_LARGE_MODEL = "gpt-4o-2024-08-06"
DEFAULT_SMALL_MODEL = "gpt-4o-mini-2024-07-18"

def natural_language_agent(model: str, system: str, output_type: Type[BaseModel] | None = None) -> Agent:
    if output_type is not None:
        return Agent(f"openai:{model}", system_prompt=system, output_type=output_type)
    else:
        return Agent(f"openai:{model}", system_prompt=system)

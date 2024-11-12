# llm 

This subdirectory contains all of the code related to nutrition management.

## Structure

The following is the structure of the subdirectory:

- `__init__.py`
- `data.py`: contains the data definitions for the nutrition tracking system.
- `assistants.py`: contains the assistant definitions for the nutrition tracking system. These are the entities that interact with the user via language model calls. 

## Language Model Tooling

This project uses `ell` for language model interaction and abstraction. Ell provides a clean interface through decorators and message handling that enables:

- Simple text-based LLM calls via `@ell.simple`
- Structured outputs with `@ell.complex` 
- Built-in versioning and tracing
- Type-safe message handling

The assistants in `assistants.py` are implemented as Language Model Programs (LMPs) using ell's decorators and APIs.



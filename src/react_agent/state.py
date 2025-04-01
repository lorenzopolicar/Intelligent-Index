"""Define the state structures for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, TypedDict, Dict, List, Any

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep
from typing_extensions import Annotated

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    data: List[Dict[str, Any]]
    namespace: str
    report: str
    feedback: str


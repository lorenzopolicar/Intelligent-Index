from pydantic import BaseModel, Field

from typing import Any, Dict, Optional

class Episode(BaseModel):  
    """Write the episode from the perspective of the agent within it. Use the benefit of hindsight to record the memory, saving the agent's key internal thought process so it can learn over time."""
    observation: str = Field(..., description="The context and setup - what happened")
    thoughts: str = Field(
        ...,
        description="Internal reasoning process and observations of the agent in the episode that let it arrive"
        ' at the correct action and result. "I ..."',
    )
    action: str = Field(
        ...,
        description="What was done, how, and in what format. (Include whatever is salient to the success of the action). I ..",
    )
    result: str = Field(
        ...,
        description="Outcome and retrospective. What did you do well? What could you do better next time? I ...",
    )

class GraphInvocationRequest(BaseModel):
    data: Any | None = None
    namespace: str
    feedback: str | None = None
    approve: str | None = None


class GraphResponse(BaseModel):
    status: str    
    result: Dict[str, Any] = None
    human_interrupt: Dict[str, Any] = None

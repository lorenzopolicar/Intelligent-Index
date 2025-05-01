from fastapi import FastAPI, HTTPException, Body, Query
from typing import Any, Dict, Optional
from pydantic import BaseModel
import uvicorn
import asyncio

from langgraph.types import Command
# Assume your compiled graph (intelligent_index) and memory store (store) are imported from your project:
from react_agent.graph import intelligent_index
from react_agent.utils import load_postgres_store
from react_agent.utils import initialize_rag
from react_agent.schemas import GraphInvocationRequest, GraphResponse

store = load_postgres_store()
rag = asyncio.run(initialize_rag())
app = FastAPI()

# Helper function: construct thread configuration from namespace.
def get_thread_config(namespace: str):
    return {"configurable": {"thread_id": namespace}}

def check_for_interrupt(thread_config: dict) -> Optional[Dict[str, Any]]:
    """
    Helper function to check if the latest graph state indicates a human interrupt.
    This implementation assumes that your graph state (obtained via get_state)
    exposes tasks with an `interrupts` attribute.
    """
    state = intelligent_index.get_state(thread_config)
    
    if state and hasattr(state, "tasks") and any(task.interrupts for task in state.tasks):
        # For demonstration, we return a simple message.
        # You could extract more details from the pending Interrupt objects.
        return state.tasks[-1].interrupts[-1].value
    return None

@app.post("/invoke", response_model=GraphResponse)
def invoke_graph(request: GraphInvocationRequest):
    # Determine if the user is sending an initial invocation or a human response.
    # For resume, the namespace must be provided.
    if request.data is not None and request.namespace is not None:
        # Initial invocation
        thread_config = {"configurable": {"thread_id": request.namespace}}
        initial_state = {"data": request.data, "namespace": request.namespace}
        try:
            result = intelligent_index.invoke(initial_state, config=thread_config)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    elif (request.approve is not None or request.feedback is not None) and request.namespace is not None:
        # Human response/resume.
        thread_config = {"configurable": {"thread_id": request.namespace}}
        # Prepare a resume input dictionary.
        resume_input = {}
        if request.approve is not None:
            resume_input["approve"] = request.approve
        if request.feedback is not None:
            resume_input["feedback"] = request.feedback
        try:
            result = intelligent_index.invoke(Command(resume=resume_input), config=thread_config)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="Invalid request payload. Provide either initial invocation (data + namespace) or resume input (approve/feedback + namespace).")

    # Check if the graph is waiting for human input.
    human_interrupt = check_for_interrupt(thread_config)
    if human_interrupt:
        return GraphResponse(status="waiting", human_interrupt=human_interrupt)
    else:
        return GraphResponse(status="final", result=result)

@app.post("/set-instructions")
def set_instructions(namespace: str = Query(...), instructions: str = Body(...)):
    """
    Endpoint to set instructions for a specific namespace.
    """
    store.put(("instructions",), key=namespace, value={"prompt": instructions})
    return {"namespace": namespace, "instructions": instructions}

# GET /retrieve-instructions endpoint: returns the instructions for a namespace
@app.get("/retrieve-instructions", response_model=Dict[str, str])
def retrieve_instructions(namespace: str = Query(...)):
    instructions_item = store.get(("instructions",), key=namespace)
    if instructions_item and "prompt" in instructions_item.value:
        return {"namespace": namespace, "instructions": instructions_item.value["prompt"]}
    else:
        raise HTTPException(status_code=404, detail="Instructions not found for given namespace.")

@app.post("/set-short-term-report")
def set_short_term_report(namespace: str = Query(...), report: str = Body(...)):
    """
    Endpoint to manually set a short-term report for a specific namespace.
    """
    store.put(("stm",), key=namespace, value={"report": report})
    return {"namespace": namespace, "short_term_report": report}

# GET /retrieve-short-term endpoint: returns the STM report for a namespace
@app.get("/retrieve-short-term", response_model=Dict[str, str])
def retrieve_short_term(namespace: str = Query(...)):
    stm_item = store.get(("stm",), key=namespace)
    if stm_item and "report" in stm_item.value:
        return {"namespace": namespace, "short_term_report": stm_item.value["report"]}
    else:
        raise HTTPException(status_code=404, detail="Short term report not found for given namespace.")

# GET /retrieve endpoint: returns search results for a given query
@app.get("/retrieve")
def retrieve_info(query: str = Query(...)):
    results = rag.query(query)  
    return {"query": query, "results": results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)

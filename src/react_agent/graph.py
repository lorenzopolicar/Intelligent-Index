"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import datetime, timezone
from typing import Dict, List, Literal, cast

from langgraph.graph import StateGraph, START, END

from react_agent.state import State
from react_agent.tools import store, episodic_memory_manager, prompt_optimizer
from react_agent.prompts import base_information_extraction_prompt, short_term_memory_manager_system
from react_agent.utils import data_formatter, llm, get_episodic_memory

from langchain_core.prompts import ChatMessagePromptTemplate
from langchain_core.messages import AIMessage, HumanMessage

from langgraph.types import interrupt, Command

# Node: Generate report based on data
async def generate_report(state):
    """
    Extracts information
    """
    data = state.get("data", [])
    namespace = state.get("namespace")

    if not data or not namespace: 
        return state

    instructions_item = store.get(("instructions",), key=f"{namespace}")
    
    if not instructions_item:
        store.put(("instructions",), key=f"{namespace}", value={"prompt": base_information_extraction_prompt})
        instructions = base_information_extraction_prompt
    
    instructions = instructions_item.value["prompt"]
    stm_item = store.get(("stm"), key=f"{namespace}")
    
    stm = ""

    if stm_item:
        stm = stm_item.value["report"]
    
    instructions += f"\n\nShort Term Memory: {stm}"

    episodic_memory = get_episodic_memory(namespace, instructions, data, store)
    
    instructions += episodic_memory

    prompt = ChatMessagePromptTemplate.from_messages(
        [
            ("system", instructions),
            ("placeholder", "{messages}")
        ]
    )

    prompt = prompt.format(messages=[HumanMessage(content=data_formatter(data))])
    response = llm.invoke(prompt)
    return {"messages": [response], "report": response}

# Node: Ask for human approval or feedback.
def human_approval(state: State) -> Command[Literal["refine_report", "finalize_report"]]:
    # Pause execution and show the generated report for review.
    feedback = interrupt({
        "question": "Approve to finalize or provide feedback for refinement.",
        "report": state.get("report", "No report generated")
    })

    # Expecting feedback in the form of a dict.
    # Example approved feedback: {"approve": True}
    # Example for refinement: {"approve": False, "edits": "Please adjust the tone to be more formal."}
    if isinstance(feedback, dict) and feedback.get("approve") is True:
        return Command(goto="finalize_report")
    else:
        edits = feedback.get("feedback", "")
        message = HumanMessage(content=f"Report needs refinement. Feedback: {edits}")
        return Command(goto="refine_report", update={"messages": [message], "feedback": edits})

# Node: Refine the report based on the human's feedback.
def refine_report(state: State) -> State:
    messages = state.get("messages", [])
    
    # Craft a prompt that instructs the LLM to refine the report based on the feedback.
    refine_prompt = (
        "The following report needs refinement based on the feedback provided.\n"
        "Please provide a refined version of the report."
    )

    prompt = ChatMessagePromptTemplate.from_messages(
        [
            ("system", refine_prompt),
            ("placeholder", "{messages}")
        ]
    )

    prompt = prompt.format(messages=messages)

    # Generate the refined report.
    refined_report = llm.invoke(prompt)
    return {"messages": [refined_report], "report": refined_report}

# Node: Finalize the report when approved.
def finalize_report(state: State) -> State:
    messages = state.get("messages", [])
    feedback_given = state.get("feedback")
    namespace = state.get("namespace")
    report = state.get("report", "")
    if not feedback_given:
        return state
    
    # Captures episodic memory 
    episodic_memory_manager.invoke({"messages": messages}, config={"configurable": {"namespace": namespace}})

    # Optimises namespace prompt
    trajectories = [(messages, None)]
    prompt = store.get(("instructions",), key=f"{namespace}").value["prompt"]
    updated_prompt = prompt_optimizer.invoke({"prompt": prompt, "trajectories": trajectories})

    store.put(("instructions",), key=f"{namespace}", value={"prompt": updated_prompt})

    # Update STM
    stm_item = store.get(("stm"), key=f"{namespace}")
    stm = ""
    if stm_item:
        stm = stm_item.value["report"]
    
    prompt = ChatMessagePromptTemplate.from_messages(
        [
            ("system", short_term_memory_manager_system),
            ("placeholder", "{messages}")
        ]
    )

    prompt = prompt.format(messages=HumanMessage(content=f"Current STM report: {stm}\n\nNew information: {report}"))
    new_stm = llm.invoke(prompt)

    store.put(("stm",), key=f"{namespace}", value={"report": new_stm})
    return state

def capture_episode(state):
    pass

def optimise_prompt(state):
    pass

def update_short_term_memory(state):
    pass

# Build the agent graph.
graph = StateGraph(State)
graph.add_node("generate_report", generate_report)
graph.add_node("human_approval", human_approval)
graph.add_node("refine_report", refine_report)
graph.add_node("finalize_report", finalize_report)

graph.add_edge(START, "generate_report")

# Define transitions between nodes:
# After generating the report, go to human approval.
graph.add_edge("generate_report", "human_approval")

# After refining, go back to human approval for review.
graph.add_edge("refine_report", "human_approval")

graph.add_edge("finalize_report", END)

# Compile the graph with a checkpointer to support interrupts.
compiled_graph = graph.compile(checkpointer="your_checkpointer")

compiled_graph.name = "ReAct Agent"  # This customizes the name in LangSmith

from IPython.display import Image, display
image_data = compiled_graph.get_graph().draw_mermaid_png()

# Save to a file
with open("intelligent_index.png", "wb") as f:
    f.write(image_data)
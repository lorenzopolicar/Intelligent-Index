"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import datetime, timezone
from typing import Dict, List, Literal, cast

from langgraph.graph import StateGraph, START, END

from react_agent.state import State
from react_agent.prompts import base_information_extraction_prompt, short_term_memory_manager_system
from react_agent.utils import data_formatter, get_episodic_memory, initialize_rag, get_llm, get_advanced_llm, load_postgres_store
from react_agent.schemas import Episode

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage

from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from langmem import create_memory_store_manager, create_prompt_optimizer


import asyncio

# Set up

llm = get_llm()
advanced_llm = get_advanced_llm()
store = load_postgres_store()


episodic_memory_manager = create_memory_store_manager(
    llm,
    namespace=("episodes", "{namespace}"),
    schemas=[Episode],
    instructions="Extract exceptional examples of noteworthy information gathering and analysis scenarios, including what made them effective.",
    enable_inserts=True,
    store=store
)

# Create optimizer
prompt_optimizer = create_prompt_optimizer(
    llm,
    kind="metaprompt",  
    config={"max_reflection_steps": 3},
)


# Node: Generate report based on data
def generate_report(state: State) -> State:
    """
    Generates a report based on data provided
    """
    data = state.get("data", [])
    namespace = state.get("namespace")

    if not data or not namespace: 
        return state

    # Getting the current prompt for the namespace
    instructions_item = store.get(("instructions",), key=namespace)
    
    if not instructions_item:
        store.put(("instructions",), key=namespace, value={"prompt": base_information_extraction_prompt})
        instructions = base_information_extraction_prompt
    else:
        instructions = instructions_item.value["prompt"]

    # Getting the current short term report / status for the namespace
    stm_item = store.get(("stm",), key=namespace)
    
    stm = ""

    if stm_item:
        stm = stm_item.value["report"]
    
    instructions += f"\n\nShort Term Memory: {stm}"

    # Extracting similiar episodic memory from previous interactions with namespace
    episodic_memory = get_episodic_memory(namespace, instructions, data, store)
    
    instructions += episodic_memory

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", instructions),
            ("placeholder", "{messages}")
        ]
    )

    prompt = prompt.format(messages=[HumanMessage(content=data_formatter(data))])
    response = advanced_llm.invoke(prompt)
    return {"messages": [HumanMessage(content=data), response], "report": response.content}


# Node: Ask for human approval or feedback.
def human_approval(state: State) -> Command[Literal["refine_report", "finalize_report"]]:
    """
    Pause execution and show the generated report for review.
    """
    feedback = interrupt({
        "question": "Approve to finalize or provide feedback for refinement.",
        "report": state.get("report", "No report generated")
    })

    # Expecting feedback in the form of a dict.
    # Example approved feedback: {"approve": True}
    # Example for refinement: {"feedback": "Please adjust the tone to be more formal."}
    if feedback.get("approve"):
        return Command(goto="finalize_report")
    else:
        edits = feedback.get("feedback", "")
        message = HumanMessage(content=f"Report needs refinement. Feedback: {edits}")
        return Command(goto="refine_report", update={"messages": [message], "feedback": edits})


# Node: Refine the report based on the human's feedback.
def refine_report(state: State) -> State:
    """
    Refine the report based on the human's feedback
    """
    messages = state.get("messages", [])
    
    # Craft a prompt that instructs the LLM to refine the report based on the feedback.
    refine_prompt = (
        "The following report needs refinement based on the feedback provided.\n"
        "Please provide a refined version of the report."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", refine_prompt),
            ("placeholder", "{messages}")
        ]
    )

    prompt = prompt.format(messages=messages)

    # Generate the refined report.
    refined_report = advanced_llm.invoke(prompt)
    return {"messages": [refined_report], "report": refined_report.content}


# Node: Finalize the report when approved.
def finalize_report(state: State) -> State:
    """
    Finalise report when approved and update namespace state
    """
    messages = state.get("messages", [])
    namespace = state.get("namespace")
    report = state.get("report", "")
    feedback = state.get("feedback")
    
    if feedback:
        # Captures episodic memory 
        episodic_memory_manager.invoke({"messages": messages}, config={"configurable": {"namespace": namespace}})

        # Optimises namespace prompt
        trajectories = [(messages, None)]
        prompt = store.get(("instructions",), key=namespace).value["prompt"]
        updated_prompt = prompt_optimizer.invoke({"prompt": prompt, "trajectories": trajectories})

        store.put(("instructions",), key=namespace, value={"prompt": updated_prompt})

    # Update STM
    stm_item = store.get(("stm",), key=namespace)
    stm = ""
    if stm_item:
        stm = stm_item.value["report"]
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", short_term_memory_manager_system),
            ("placeholder", "{messages}")
        ]
    )

    prompt = prompt.format(messages=[HumanMessage(content=f"Current STM report: {stm}\n\nNew information: {report}")])
    new_stm = llm.invoke(prompt)

    store.put(("stm",), key=namespace, value={"report": new_stm.content})

    # Update LongTerm
    rag = asyncio.run(initialize_rag())
    rag.insert(report)

    messages.append(AIMessage(content=f"New STM:\n{new_stm.content}"))

    return {"messages": messages}

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
checkpointer = InMemorySaver()
intelligent_index = graph.compile(checkpointer=checkpointer)

intelligent_index.name = "Intelligent Index"

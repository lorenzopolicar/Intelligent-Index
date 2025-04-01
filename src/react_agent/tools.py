"""This module provides example tools for web scraping and search functionality.

It includes a basic Tavily search function (as an example)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

from typing import Any, Callable, List, Optional, cast

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg

from langgraph.store.memory import InMemoryStore
from langmem import ReflectionExecutor, create_memory_store_manager, create_multi_prompt_optimizer
from react_agent.utils import llm, embeddings
from react_agent.schemas import Episode
from typing_extensions import Annotated

from react_agent.configuration import Configuration

store = InMemoryStore(
    index={
        "dims": 1536,
        "embed": embeddings
    }
)

async def search(
    query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[list[dict[str, Any]]]:
    """Search for general web results.

    This function performs a search using the Tavily search engine, which is designed
    to provide comprehensive, accurate, and trusted results. It's particularly useful
    for answering questions about current events.
    """
    configuration = Configuration.from_runnable_config(config)
    wrapped = TavilySearchResults(max_results=configuration.max_search_results)
    result = await wrapped.ainvoke({"query": query})
    return cast(list[dict[str, Any]], result)

memory_manager = create_memory_store_manager(
    llm,
    namespace=("memories",),
)

reflection_executor = ReflectionExecutor(memory_manager)

episodic_memory_manager = create_memory_store_manager(
    llm,
    namespace=("memories", "episodes"),
    schemas=[Episode],
    instructions="Extract exceptional examples of noteworthy information gathering and analysis scenarios, including what made them effective."
)

# Create optimizer
optimizer = create_multi_prompt_optimizer(
    "anthropic:claude-3-5-sonnet-latest",
    kind="gradient",  # Best for team dynamics
    config={"max_reflection_steps": 3},
)



TOOLS: List[Callable[..., Any]] = [search]

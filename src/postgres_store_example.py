from langgraph.store.memory import InMemoryStore
from langgraph.store.postgres import PostgresStore
from psycopg import Connection

from langmem import create_memory_store_manager, create_prompt_optimizer

from react_agent.utils import get_llm, load_postgres_store
from react_agent.schemas import Episode

store = load_postgres_store()
llm = get_llm()

def get_episodic_memory(namespace, instructions, data, store):
        similar = store.search(
            ("episodes", namespace),
            query=f"Instructions: {instructions}\n\nData:\n{data}",
            limit=1,
        )

        # Step 2: Build system message with relevant experience
        episodic_memory = "" 
        if similar:
            episodic_memory += "\n\n### EPISODIC MEMORY:"
            for i, item in enumerate(similar, start=1):
                episode = item.value["content"]
                episodic_memory += f"""
                    Episode {i}:
                    When: {episode['observation']}
                    Thought: {episode['thoughts']}
                    Did: {episode['action']}
                    Result: {episode['result']}
                """
        return episodic_memory

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

conversation = [
    {
        "role": "user",
        "content": "What's a binary tree? I work with family trees if that helps",
    },
    {
        "role": "assistant",
        "content": "A binary tree is like a family tree, but each parent has at most 2 children. Here's a simple example:\n   Bob\n  /  \\\nAmy  Carl\n\nJust like in family trees, we call Bob the 'parent' and Amy and Carl the 'children'.",
    },
    {
        "role": "user",
        "content": "Oh that makes sense! So in a binary search tree, would it be like organizing a family by age?",
    },
]

episodic_memory_manager.invoke({"messages": conversation}, config={"configurable": {"namespace": "CS"}})

episodes = get_episodic_memory("CS", "You are a CS tutor", "A binary tree is complete", store)

print(episodes)
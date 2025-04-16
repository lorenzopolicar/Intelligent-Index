from react_agent.utils import initialize_rag
import asyncio

def main():
    rag = asyncio.run(initialize_rag())
    print(rag.query("What happened on March 24"))

if __name__ == "__main__":
    main()
import asyncio
import operator
import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL")
# format: postgresql://username:password@aws-0-eu-central-1.pooler.supabase.com:6543/dbname
PSYCOPG3_DATABASE_URL = os.getenv("PSYCOPG3_DATABASE_URL")


class State(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


rate_limiter = InMemoryRateLimiter(
    requests_per_second=1,
    check_every_n_seconds=0.9,
    max_bucket_size=1,
)
llm = ChatOpenAI(
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base=OPENROUTER_BASE_URL,
    model_name="google/gemini-2.5-pro",
    rate_limiter=rate_limiter,
)


async def test_node(state: State):
    print("Error will happen once the below line is executed")
    message = await llm.ainvoke(state["messages"])
    print(message)
    return {"messages": [message]}


async def main():
    workflow = StateGraph(State)
    workflow.add_node("test_node", test_node)
    workflow.add_edge(START, "test_node")
    workflow.add_edge("test_node", END)

    async with AsyncPostgresSaver.from_conn_string(PSYCOPG3_DATABASE_URL, pipeline=False) as checkpointer:
        checkpointer.conn.prepare_threshold = None  # required to avoid issues with pgbouncer / supavisor
        await checkpointer.setup()
        graph = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "12"}}
        
        ### ERROR ABOUT TO HAPPEN ###
        await graph.ainvoke({"messages": [HumanMessage(content="Hello, how are you?")]}, config=config)
        


if __name__ == "__main__":
    asyncio.run(main())

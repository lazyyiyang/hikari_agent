from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import os
import langchain

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai.chat_models import ChatOpenAI
from template import COMPANY_AGENT_PROMPT
from dotenv import load_dotenv

load_dotenv(override=True)
langchain.debug = True

llm = ChatOpenAI(
    api_key=os.getenv("API_KEY", ""),  # type: ignore
    base_url="https://api.deepseek.com",
    model="deepseek-chat",
)


async def data_analysis(query):
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            # Get tools
            tools = await load_mcp_tools(session)
            agent = create_react_agent(llm, tools)
            agent_response = await agent.ainvoke({"messages": query})
            last_response = agent_response["messages"][-1]
            with open("result/demo.md", "w", encoding="utf-8") as f:
                f.write(last_response.content)
    return last_response.content


if __name__ == "__main__":
    query = COMPANY_AGENT_PROMPT.format(
        company="浦发银行",
    )
    result = asyncio.run(data_analysis(query))
    print(result)

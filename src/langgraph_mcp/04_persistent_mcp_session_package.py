from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import os
from contextlib import asynccontextmanager, AsyncExitStack
from langchain_core.messages import SystemMessage
from pathlib import Path
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import tools_condition, ToolNode
from pydantic import BaseModel
from typing import Annotated, List
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph_mcp.configuration import get_llm
from langgraph_mcp.streaming_utils import (
    chat_endpoint_handler,
    truncate_messages_safely,
)

"""
LangGraph Agent with External MCP Packages (stdio)

This example shows:
- Local MCP servers (math, weather)  
- External MCP packages installed via uv (office-word-mcp-server)

Flow: User types in web interface → Agent uses tools → Response streams back

Example:
  User: "Calculate 5 * 8, then create a Word doc called 'result.docx' with the answer"
  Agent: *calls math multiply(5, 8) then word create_document()*
  Result: "5 * 8 = 40. Created result.docx with the result."
"""

# put verbose to true to see chat and tool results in terminal
VERBOSE = True


# Define the state of the graph
class MessageState(BaseModel):
    messages: Annotated[List, add_messages]


def create_assistant(llm_with_tools):
    """Create an assistant function with access to the LLM"""
    system_prompt = SystemMessage(
        content="""
You are an Expert Developer Relations Engineer automating technical content creation using MCP tools.


### TOOL RULES:

1. BROWSER MCP:
   - When the user asks to browse, search, or visit a website: IMMEDIATELY call browser tools.
     Do NOT ask the user to connect first — just try browser_navigate and handle errors if they happen.
   - Workflow: browser_navigate → browser_wait (2) → browser_snapshot → browser_click/browser_type
   - Always get refs from the latest browser_snapshot before typing or clicking.
   - Use a dedicated Chrome tab (not localhost:8000). User connects via extension → Connect.
   - If a tool fails with "No tab with given id" or connection error: then tell user to open a
     new Chrome tab, click Connect, and retry.
   - Never close or manually interact with the connected tab during automation.

2. GIT:
   - Check git_status before git_add (exclude .DS_Store)
   - Only stage files, never commit to main

3. STATE MANAGEMENT:
   - Filesystem is your memory - read files before editing
                """
    )


    async def assistant(state: MessageState):
        # Increase max_history to prevent state loss in multi-step workflows
        messages = truncate_messages_safely(state.messages, max_history=40)
        messages = [system_prompt] + messages
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    return assistant


def build_graph(tools):
    """Build and return the LangGraph ReAct agent with MCP tools"""
    llm = get_llm("openai")
    llm_with_tools = llm.bind_tools(tools)

    builder = StateGraph(MessageState)
    builder.add_node("assistant", create_assistant(llm_with_tools))
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


def get_mcp_servers(current_dir: Path) -> dict:
    """Define all MCP servers (local + external packages)."""
    return {
        
        "browsermcp": {
            "command": "npx",
            "args": ["-y", "@browsermcp/mcp"],
            "transport": "stdio",
        },
        
        "filesystem": {
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                str(current_dir.parent.parent),
            ],
            "transport": "stdio",
        },
        
        
        # "local_math": {
        #     "command": "python",
        #     "args": [str(current_dir / "local_mcp_servers" / "math_server.py")],
        #     "transport": "stdio",
        # },
        
        # "project": {
        #     "command": "python",
        #     "args": [str(current_dir / "local_mcp_servers" / "project_server.py")],
        #     "transport": "stdio",
        # },
        
        # "filesystem": {
        #     "command": "npx",
        #     "args": [
        #         "-y",
        #         "@modelcontextprotocol/server-filesystem",
        #         str(current_dir.parent.parent),
        #     ],
        #     "transport": "stdio",
        # },
        
        # "git": {
        #     "command": "uvx",
        #     "args": ["mcp-server-git"],
        #     "transport": "stdio",
        # },
        
        # "ai-diagram-maker": {
        #     "command": "npx",
        #     "args": ["-y", "ai-diagram-maker-mcp@latest"],
        #     "env": {"ADM_API_KEY": os.getenv("ADM_API_KEY", "")},
        #     "transport": "stdio",
        # },
        
        # "firecrawl-mcp": {
        #     "command": "npx",
        #     "args": ["-y", "firecrawl-mcp"],
        #     "env": {"FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY", "")},
        #     "transport": "stdio",
        # },
        
        # "office_word": {
        #     "command": "uv",
        #     "args": ["tool", "run", "--from", "office-word-mcp-server", "word_mcp_server"],
        #     "transport": "stdio",
        # },
    }


async def setup_langgraph_app():
    """Setup the LangGraph app with MCP tools using one persistent session per server."""
    current_dir = Path(__file__).parent
    all_servers = get_mcp_servers(current_dir)
    client = MultiServerMCPClient(all_servers)

    stack = AsyncExitStack()
    await stack.__aenter__()
    try:
        tools = []
        for name in all_servers:
            session = await stack.enter_async_context(client.session(name))
            tools.extend(await load_mcp_tools(session, server_name=name))
    except Exception:
        await stack.aclose()
        raise

    print(f"\nLoaded {len(tools)} tools from {len(all_servers)} server(s):")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")

    if "browsermcp" in all_servers:
        print(
            "\n>>> Browser MCP setup:"
            "\n    1. Open a NEW Chrome tab (not localhost:8000 chat)"
            "\n    2. Click Browser MCP extension → Connect"
            "\n    3. Leave that tab alone while chatting <<<\n"
        )

    return build_graph(tools), stack


@asynccontextmanager
async def lifespan(app: FastAPI):
    langgraph_app, mcp_stack = await setup_langgraph_app()
    app.state.langgraph_app = langgraph_app
    try:
        yield
    finally:
        await mcp_stack.aclose()


app = FastAPI(lifespan=lifespan)

# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root():
    return RedirectResponse(url="/static/chat.html")


@app.post("/chat")
async def chat_endpoint(
    request: Request, user_input: str = Form(...), thread_id: str = Form(None)
):
    print("Received user_input:", user_input)
    return await chat_endpoint_handler(request, user_input, thread_id, VERBOSE)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

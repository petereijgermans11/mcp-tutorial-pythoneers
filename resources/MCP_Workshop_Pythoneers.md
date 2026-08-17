MCP & LangGraph Workshop


## PART 1

Connect to local MCP servers with Claude Desktop

Leer hoe je Claude Desktop kunt uitbreiden met lokale MCP-servers om toegang tot het bestandssysteem en andere krachtige integraties mogelijk te maken.

Download Claude Desktop en volg deze tutorial:

<https://modelcontextprotocol.io/docs/develop/connect-local-servers>


## PART 2



### `01_no_mcp_langgraph_agent.py 

This file demonstrates a basic LangGraph ReAct (Reasoning and Acting) agent that uses local Python functions as tools.`


The agent has three tools available: add, multiply, and divide. These are simple Python functions that are bound to the LLM, allowing it to call them when needed. This demonstrates the core LangGraph pattern without MCP integration. In later examples, we'll see how MCP servers replace these local functions.

The agent follows a simple flow:

1. Human Question → The user asks a question

2. Assistant → The LLM decides whether to go to end node, or to call the tool(s) node

3. Tool Execution → The selected tool(s) are executed

4. Assistant → The LLM summarizes the tool execution and

goes to step 2; go to end node, or call tool(s) node once more.


#### Exercise 1: Which part(s) of the function (doc string, type hints, function body code, function body comments) output will NOT be included in the MCP JSON format when the tool is sent to the LLM?


___________________________________________________________


#### Exercise 2: Run File:

poetry run python 01_no_mcp_langgraph_agent.py

Read the result.


What solutions can we suggest regarding the missing Word document? (just ideas)

___________________________________________________________


#### Exercise 3: Is the agent limited to using only 1 tool call per question, or can it chain multiple tool calls together? Try asking a question that requires multiple operations, such as: "What is (3 + 4) * 2?" Observe how many tool calls are made. 
___________________________________________________________



#### Exercise 4: Try asking this question:

“I have 8 pizzas and 4 friends. How many does everyone get, and if we bake 2 more, how many pizzas will we have in total?”
___________________________________________________________



#### Exercise 5: How does the Graph know which tool to call? Where is this information stored? What problem might arise if we have too many tools available?
 ___________________________________________________________



## PART 3



### `02_mcp_stdio_local.py`


This is a LangGraph ReAct agent that loads tools from local MCP servers running as subprocesses via stdio transport (found in the local_mcp_servers folder).

Unlike PART 2, which uses direct Python functions, PART 3 uses tools exposed through @mcp.tool() decorators, demonstrating the transition from local tooling to MCP-based servers. These servers are fully compatible with standard MCP clients such as LangChain’s MultiServerMCPClient.


#### Exercise 1: Compare the tools available in file 01.py vs file 02.py. Are they the same? What's the difference in how they're defined and loaded? 
___________________________________________________________



#### Exercise 2: Try asking a question that requires both math and weather tools: "Wat's 5 * 3 and what's the weather in Paris?" Observe how the agent chains multiple tool calls from different MCP-servers. ___________________________________________________________



#### Exercise 3: What is stdio transport? How does it differ from HTTP transport? When would you choose one over the other? ___________________________________________________________



#### Exercise 4: In file 02, the `assistant` function is defined as `async def assistant(state: MessageState)`.


What is the benefit for it to be async?

__________________________________________________________


#### Exercise 5: see slide 26  build your own “project_server.py”

Build a MCP server that understands the codebase of this project.
This MCP server contains the following tools:

- list_files()
- list_python_files()
- project_stats()
- risk_analysis()
- ect.....

## PART 4



### `03_mcp_stdio_external_package.py`


LangGraph agent combining local MCP servers with external MCP packages (like office-word-mcp-server) via stdio. This file includes a FastAPI web interface with streaming chat. This example demonstrates how to integrate both locally developed MCP servers and external packages from the MCP ecosystem. User accesses FastAPI web interface at http://localhost:8000/chat or https://127.0.0.1:8000/chat


#### Exercise 1: What is the danger of using external packages from MCP? What security considerations should you keep in mind when running external MCP servers? 
___________________________________________________________



#### Exercise 2.a: How many tool calls are loaded from the Word-mcp server? Check the console output when the server starts and scan the list of all the tools available from the office-word-mcp-server. Do you think the LLM has enough context for when to use what tool? 
___________________________________________________________



#### Exercise 2.b: How could we guide the LLM to have a better understanding of when to use what tool? Hint: system prompt


Pas system prompt aan!

___________________________________________________________


#### Exercise 3: Try to make a query that combines the weather server, math server and creates a word document with the answer of your query. Make sure to give the word document a name.docx.


For example: "What's the weather in Paris and what's 15 * 7? Create a word document called results.docx with both answers." ___________________________________________________________


#### Exercise 4: Compare the server configuration for local servers vs external packages. Where is the uv package installed? ___________________________________________________________



#### Exercise 5: The FastAPI endpoint uses `async def chat_endpoint()`.


How does this enable multiple users to use the web interface simultaneously? What would happen if it were synchronous? ___________________________________________________________


#### Exercise 6:


Search and try more external MCP servers via https://mcpmarket.com/

___________________________________________________________


### Bonus


Add another node to the graph in 01_no_mcp_langgraph_agent.py

The extra node checks if the question is about math (addition, multiplication, or division) before proceeding to the assistant. If the question is not about math, bind to the END node.

Steps:

1. Create a node validate_math_question(state: MessageState) that checks if the user question’s intent for math

2. Add this as a node in the graph between START and "assistant"

3. Add conditional logic to either proceed to the assistant or return an error message


## Visuals from the original document


The following images were embedded in the original DOCX:


![Workshop image](assets/image1.png)


![Workshop image](assets/image2.png)

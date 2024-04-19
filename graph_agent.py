import json
import operator

from langchain.agents import tool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import BaseMessage, FunctionMessage
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolInvocation, ToolExecutor
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence


# 使用するモデルを選択。
# 予算が許す場合はgpt-4-turboを推奨
MODEL = "gpt-3.5-turbo-0125"
# MODEL = "gpt-4-turbo"


# Agentの使用できるToolを定義
# 必要に応じて、他のToolを追加してください
@tool
async def ddg_search(query: str) -> str:
    """Searches DuckDuckGo for a query and returns the results."""
    search = DuckDuckGoSearchResults()
    return search.invoke(query)


# toolを配列にまとめて、ToolExecutorに渡す
# toolを追加した場合は、忘れずにここに追加してください
tools = [ddg_search]
tool_executor = ToolExecutor(tools)


# 以降はlanggraphのサンプルコードをほぼそのまま使用しています
# https://github.com/langchain-ai/langgraph/blob/main/examples/async.ipynb

# We will set streaming=True so that we can stream tokens
# See the streaming section for more information on this.
model = ChatOpenAI(model=MODEL, temperature=0, streaming=True)

functions = [convert_to_openai_function(t) for t in tools]
model = model.bind_functions(functions)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


# Define the function that determines whether to continue or not
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we finish
    if "function_call" not in last_message.additional_kwargs:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"
    

# Define the function that calls the model
async def call_model(state):
    messages = state["messages"]
    response = await model.ainvoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


# Define the function to execute tools
async def call_tool(state):
    messages = state["messages"]
    # Based on the continue condition
    # we know the last message involves a function call
    last_message = messages[-1]
    # We construct an ToolInvocation from the function_call
    action = ToolInvocation(
        tool=last_message.additional_kwargs["function_call"]["name"],
        tool_input=json.loads(
            last_message.additional_kwargs["function_call"]["arguments"]
        ),
    )
    # We call the tool_executor and get back a response
    response = await tool_executor.ainvoke(action)
    # We use the response to create a FunctionMessage
    function_message = FunctionMessage(content=str(response), name=action.tool)
    # We return a list, because this will get added to the existing list
    return {"messages": [function_message]}

# main.pyから呼び出して使いたいので、ここだけ関数化
def create_agent():
    # Define a new graph
    workflow = StateGraph(AgentState)

    # Define the two nodes we will cycle between
    workflow.add_node("agent", call_model)
    workflow.add_node("action", call_tool)

    # Set the entrypoint as `agent`
    # This means that this node is the first one called
    workflow.set_entry_point("agent")

    # We now add a conditional edge
    workflow.add_conditional_edges(
        # First, we define the start node. We use `agent`.
        # This means these are the edges taken after the `agent` node is called.
        "agent",
        # Next, we pass in the function that will determine which node is called next.
        should_continue,
        # Finally we pass in a mapping.
        # The keys are strings, and the values are other nodes.
        # END is a special node marking that the graph should finish.
        # What will happen is we will call `should_continue`, and then the output of that
        # will be matched against the keys in this mapping.
        # Based on which one it matches, that node will then be called.
        {
            # If `tools`, then we call the tool node.
            "continue": "action",
            # Otherwise we finish.
            "end": END,
        },
    )

    # We now add a normal edge from `tools` to `agent`.
    # This means that after `tools` is called, `agent` node is called next.
    workflow.add_edge("action", "agent")

    # Finally, we compile it!
    # This compiles it into a LangChain Runnable,
    # meaning you can use it as you would any other runnable
    app = workflow.compile()

    # appを返す
    return app
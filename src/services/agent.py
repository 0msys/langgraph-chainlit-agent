from typing import Annotated, Literal
from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from services.tools.vision import vision
from services.tools.ddg_search import ddg_search


class State(TypedDict):
    messages: Annotated[list, add_messages]


class SingleAgent:
    """
    LangGraphを使用したSingle Agentのクラス
    """

    def __init__(self, system_prompt: str, model_version: str = "gpt-4o-mini"):
        self.system_prompt = system_prompt
        tools = [ddg_search, vision]
        tool_node = ToolNode(tools)
        self.tool_names = [tool.name for tool in tools]

        model = ChatOpenAI(model=model_version, temperature=0, streaming=True)

        self.model = model.bind_tools(tools)

        workflow = StateGraph(State)

        workflow.add_node("agent", self.__call_model)
        workflow.add_node("tools", tool_node)

        workflow.add_edge(START, "agent")

        workflow.add_conditional_edges(
            "agent",
            self.__should_continue,
        )

        workflow.add_edge("tools", "agent")

        self.app = workflow.compile()

    def __should_continue(self, state: State) -> Literal["__end__", "tools"]:
        messages = state["messages"]
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return END
        # Otherwise if there is, we continue
        else:
            return "tools"

    async def __call_model(self, state: State, config: RunnableConfig):
        messages = state["messages"]
        response = await self.model.ainvoke(messages, config)
        return {"messages": response}

    async def astream_events(self, inputs):
        """
        StreamingでLLMの出力を取得する

        Args:
            inputs: HumanMessageのリスト

        Yields:
            dict: Streaming出力の情報
        """
        output = ""
        async for event in self.app.astream_events(
            # inputsの先頭にsystem_promptを追加
            {"messages": [SystemMessage(content=self.system_prompt)] + inputs},
            version="v1",
        ):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                # LLMのStreaming出力を取得
                content = event["data"]["chunk"].content
                if content:
                    output = {"kind": kind, "content": content}
                    yield output

            elif kind == "on_tool_start" and event["name"] in self.tool_names:
                # Toolの開始イベントを取得
                output = {
                    "kind": kind,
                    "tool_name": event["name"],
                    "run_id": event["run_id"],
                    "tool_input": event["data"].get("input"),
                }
                # print(f"tool_input: {event}")
                yield output

            elif kind == "on_tool_end" and event["name"] in self.tool_names:
                # Toolの終了イベントを取得
                output = {
                    "kind": kind,
                    "tool_name": event["name"],
                    "run_id": event["run_id"],
                    "tool_input": event["data"].get("input"),
                    "tool_output": event["data"].get("output"),
                }
                # print(f"tool_output: {event}")
                yield output

    async def ainvoke(self, inputs: list):
        """
        LLMの出力を取得する

        Args:
            inputs: Messageのリスト

        Returns:
            dict: LLMの出力とToolの出力
        """
        output_message = ""
        tool_outputs = []
        async for output in self.astream_events(inputs):
            if isinstance(output, dict) and "content" in output:
                if output["kind"] == "on_chat_model_stream":
                    output_message += output["content"]
            elif output["kind"] == "on_tool_end":
                tool_outputs.append(
                    {
                        "name": output["tool_name"],
                        "input": output["tool_input"],
                        "output": output["tool_output"],
                    }
                )
        output = {"content": output_message, "tool_outputs": tool_outputs}
        return output

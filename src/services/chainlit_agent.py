import chainlit as cl
import pytz

from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime

from services.agent import SingleAgent


class ChainlitAgent(SingleAgent):

    def __init__(
        self,
        system_prompt: str,
    ):
        super().__init__(system_prompt=system_prompt)

    async def on_message(self, msg: cl.Message, inputs: list):

        content = msg.content

        # 添付ファイルの情報を取得
        attachment_file_text = ""

        for element in msg.elements:
            attachment_file_text += f'- {element.name} (path: {element.path.replace("/workspace", ".")})\n'  # agentが参照するときは./files/***/***.pngのようになるので、それに合わせる

        if attachment_file_text:
            content += f"\n\n添付ファイル\n{attachment_file_text}"

        # 　現在の日時を取得(JST)
        now = datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S %Z")

        content += f"\n\n(入力日時: {now})"

        # ユーザーのメッセージを履歴に追加
        inputs.append(HumanMessage(content=content))

        res = cl.Message(content="")
        steps = {}
        async for output in self.astream_events(inputs):
            if output["kind"] == "on_chat_model_stream":
                await res.stream_token(output["content"])
            elif output["kind"] == "on_tool_start":
                async with cl.Step(name=output["tool_name"], type="tool") as step:
                    step.input = output["tool_input"]
                    steps[output["run_id"]] = step
            elif output["kind"] == "on_tool_end":
                step = steps[output["run_id"]]
                step.output = output["tool_output"]
                await step.update()

        await res.send()

        return AIMessage(content=res.content)

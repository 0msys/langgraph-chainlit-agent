import chainlit as cl

from langchain_core.messages import HumanMessage, AIMessage

from graph_agent import create_agent


@cl.on_chat_start
async def on_chat_start():
    # セッションが開始したら、エージェントを作成してセッションに保存
    app = create_agent()
    cl.user_session.set("app", app)

    # メッセージの履歴を保存するためのリストをセッションに保存
    cl.user_session.set("inputs", {"messages": []})


@cl.on_message
async def on_message(msg: cl.Message):
    # メッセージを受け取ったら、セッションからエージェントとメッセージの履歴を取得
    app = cl.user_session.get("app")
    inputs = cl.user_session.get("inputs")

    # ユーザーのメッセージを履歴に追加
    inputs["messages"].append(HumanMessage(content=msg.content))

    # 空のメッセージを送信して、ストリーミングする場所を用意しておく
    agent_message = cl.Message(content="")
    await agent_message.send()
    
    chunks = []

    # エージェントを実行
    async for output in app.astream_log(inputs, include_types=["llm"]):
        for op in output.ops:
            if op["path"] == "/streamed_output/-":
                # 途中経過をステップに表示する
                edge_name = list(op["value"].keys())[0]
                message = op["value"][edge_name]["messages"][-1]
                
                # actionノードの場合は、メッセージの内容を表示(Toolの戻り値が表示される)
                if edge_name == "action":
                    step_name = message.name
                    step_output = "```\n" + message.content + "\n```"

                # agentノードの場合は、function callの場合は、関数名と引数を表示
                elif hasattr(message, "additional_kwargs") and message.additional_kwargs:
                    step_name = edge_name
                    step_output = f"function call: {message.additional_kwargs["function_call"]["name"]}\n\n```\n{message.additional_kwargs["function_call"]["arguments"]}\n```"
                
                # その他のパターンではとりあえず何も表示しない
                else:
                    continue

                # ステップを送信
                async with cl.Step(name=step_name) as step:
                    step.output = step_output
                    await step.update()

            elif op["path"].startswith("/logs/") and op["path"].endswith(
                "/streamed_output_str/-"
            ):
                # 最終的な応答を、あらかじめ用意しておいたメッセージにストリーミング
                chunks.append(op["value"])
                await agent_message.stream_token(op["value"])

        # ストリーミングした応答を結合して、最終的な応答を作成
        res = "".join(chunks)

    # 最終的な応答を履歴に追加し、セッションに保存
    inputs["messages"].append(AIMessage(content=res))
    cl.user_session.set("inputs", inputs)
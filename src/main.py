import chainlit as cl

from services.chainlit_agent import ChainlitAgent


@cl.on_chat_start
async def on_chat_start():
    system_prompt = "あなたは最高のアシスタントチャットボットです。どんな依頼にも丁寧に最高のサービスを提供します。"
    chainlit_agent = ChainlitAgent(
        system_prompt=system_prompt,
    )
    cl.user_session.set("chainlit_agent", chainlit_agent)


@cl.on_message
async def on_message(msg: cl.Message):

    inputs = cl.user_session.get("inputs", [])
    chainlit_agent = cl.user_session.get("chainlit_agent")

    output = await chainlit_agent.on_message(msg, inputs)
    inputs.append(output)
    cl.user_session.set("inputs", inputs)

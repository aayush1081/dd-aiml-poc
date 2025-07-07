from agents import Runner
import asyncio
import nest_asyncio

nest_asyncio.apply()

async def run_chatbot(messages, agent):
    return await Runner.run(agent, input=messages)

def get_response(messages, agent):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        return loop.run_until_complete(run_chatbot(messages, agent))
    else:
        return asyncio.run(run_chatbot(messages, agent))

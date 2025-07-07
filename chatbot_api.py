# chat_api.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from agents import Runner
from AI_orchestration import customer_service_agent
from cosmos_db_streamlit_helper import create_cosmos_resources
from datetime import datetime
import asyncio
import nest_asyncio

nest_asyncio.apply()
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

container = create_cosmos_resources()

class Message(BaseModel):
    role: str
    content: str

class ChatPayload(BaseModel):
    messages: List[Message]

async def run_agent_async(messages):
    return await Runner.run(customer_service_agent, input=messages)

@app.post("/chat")
async def chat(payload: ChatPayload, request: Request):
    session_start = datetime.now().timestamp()
    ip = request.client.host
    msg_id = 1

    # Save user messages
    for msg in payload.messages:
        item = {
            'id': f"{msg_id}-{session_start}",
            'msg_seq': msg_id,
            'session_start': str(session_start),
            'ip': ip,
            'role': msg.role,
            'content': msg.content
        }
        container.upsert_item(item)
        msg_id += 1

    # Run agent and get response
    response = await run_agent_async([m.dict() for m in payload.messages])

    # Save assistant message
    item = {
        'id': f"{msg_id}-{session_start}",
        'msg_seq': msg_id,
        'session_start': str(session_start),
        'ip': ip,
        'role': 'assistant',
        'content': response.final_output
    }
    container.upsert_item(item)

    return {
        "response": response.final_output
    }

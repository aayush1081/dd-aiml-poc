import streamlit as st
import random
import time
from AI_orchestration import customer_service_agent
from cosmos_db_streamlit_helper import get_remote_ip, create_cosmos_resources
import asyncio
from agents import Runner
import nest_asyncio
import logging
from datetime import datetime
nest_asyncio.apply()
logger = logging.getLogger(__name__)

# def run_agent(customer_service_agent):
#     async def inner():
#         return await Runner.run(customer_service_agent, input=st.session_state.messages)
#     return asyncio.run(inner())

async def run_agent_async(customer_service_agent):
    return await Runner.run(customer_service_agent, input=st.session_state.messages)

def run_agent(customer_service_agent):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        return loop.run_until_complete(run_agent_async(customer_service_agent))
    else:
        return asyncio.run(run_agent_async(customer_service_agent))

st.title("NOC chatbot demo - POC")
st.subheader("AI can make mistakes")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.msg_id = 1
    st.session_state.session_start = datetime.now().timestamp()
    st.session_state.client_ip = get_remote_ip()
    st.session_state.container = create_cosmos_resources()
    

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask me something..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    ## Add to cosmos DB
    #print(msg_id)
    item = {'id':str(st.session_state.msg_id)+'-'+str(st.session_state.session_start),
            'msg_seq':st.session_state.msg_id,
            'session_start':str(st.session_state.session_start),
            'ip':st.session_state.client_ip,
            'role':'user',
            'content':prompt}
    print('started upload')
    st.session_state.container.upsert_item(item)
    print('completed upload')
    st.session_state.msg_id+=1

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        user_prompt = st.session_state.messages[-1]
        history = st.session_state.messages[:-1]
        response = run_agent(customer_service_agent) #await Runner.run(customer_service_agent, input=st.session_state.messages )
        #print(response.raw_responses)
        st.write(response.final_output)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response.final_output})
    # Add to cosmos DB
    item = {'id':str(st.session_state.msg_id)+'-'+str(st.session_state.session_start),
            'msg_seq':st.session_state.msg_id,
            'session_start':str(st.session_state.session_start),
            'ip':st.session_state.client_ip,
            'role':'assistant',
            'content':response.final_output}
    st.session_state.container.upsert_item(item)
    st.session_state.msg_id+=1
    #print(msg_id)
    st.session_state.messages = st.session_state.messages[-5:]
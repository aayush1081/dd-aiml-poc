#!pip install google-search-results
from __future__ import annotations
import logging
import asyncio

import openai
from openai import AsyncAzureOpenAI
from agents import items, Agent, WebSearchTool, HandoffInputData, Runner, function_tool, handoff, trace, set_default_openai_client, set_tracing_disabled, OpenAIChatCompletionsModel, OpenAIResponsesModel, set_tracing_export_api_key, add_trace_processor
from agents.tracing.processors import ConsoleSpanExporter, BatchTraceProcessor
from agents.extensions import handoff_filters
import logfire
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
#logfire.configure(inspect_arguments=False)

## Tool functions
from rag_optimized import response_generator as rag, Web_search, search_vector_db
from sql_llm import response_generator as sql_llm
from prtg_sensor import get_prtg_data, get_all_sensors_for_device, get_all_downstream_sensors
from constants import openai_api_key , openai_api_version ,openai_endpoint,openai_deployment

##Create OpenAI client using Azure OpenAI
openai_client = AsyncAzureOpenAI(
    api_key=openai_api_key,
    api_version=openai_api_version,
    azure_endpoint=openai_endpoint,
    azure_deployment=openai_deployment
)

# Set the default OpenAI client for the Agents SDK
set_default_openai_client(openai_client)

# Set the API key for trace export
set_tracing_export_api_key("")
# Set up console tracing
# console_exporter = ConsoleSpanExporter()
# console_processor = BatchTraceProcessor(console_exporter)
# add_trace_processor(console_processor)
set_tracing_disabled(False)

# Configure logfire
logfire.configure(
    service_name='agentic_AI_ITSM',
    send_to_logfire=False,
    distributed_tracing=True
)
logfire.instrument_openai_agents()


## Set up functions
@function_tool
async def rag_call(user_input:str)->str:
    #history = user_input[-10:-1]
    history = []
    ''' You can use company data to answer questions for L2 engineers. You can query company data (SOPs, run books and user manuals) tol generate coherent and complete outputs. Use for more complex questions.'''
    return rag(user_input, history)

@function_tool
async def sql_call(user_input:str)->str:
    '''You are a data generation tool designed to help pull RMS data for users.
    You can take natural language inputs from user and convert to SQL query.
    This is mainly tickets data raised by users in an ITSM tool. Do not call for any generic questions.'''
    return sql_llm(user_input)

@function_tool
async def Web_search_call(user_input:str)->str:
    ''' Search the internet / web for results and more information. Only call if user explicitly asks for this.
    Do not call in reasoning steps. If there is an error, display the error as is. '''
    context = Web_search(user_input)
    return context

@function_tool
async def pure_search(user_input:str)->str:
    '''You can search company's data which includes SOPs, user manuals and runbooks and return the output it is.
    Call as a lightweight alternative for RAG'''
    context = search_vector_db(user_input,  25)
    return context

@function_tool
async def prtg_sensor_data(user_input:int)->str:
    '''You can get current information for any sensor. Make sure to get integer sensor ID as input.  
    Sample output will look like - 
        {'prtgversion': '25.1.104.1961+',
     'sensordata': {'name': 'Ping',
      'parentgroupname': '10.101.1.0/24',
      'parentdevicename': 'ADSLUSBKUP01.allieddigital.net (10.101.1.69)',
      'sensortype': 'ping',
      'interval': '90',
      'probename': 'ADSL-USA',
      'statusid': '5',
      'lastup': '45788.6232770486 [2 d 18 h 31 m ago]',
      'lastdown': '45791.3943874653 [63 s ago]',
      'lastcheck': '45791.3943874653 [63 s ago]',
      'uptime': '99.1026%',
      'uptimetime': '305 d',
      'downtime': '0.8974%',
      'downtimetime': '2 d 18 h 18 m',
      'updowntotal': '0 s  [=100% coverage]',
      'updownsince': '45483.2044816319 [308 d ago]',
      'parentdeviceid': '76131',
      'lastvalue': '',
      'lastmessage': 'Destination host unreachable (ICMP error # 11003)',
      'statustext': 'Down',
      'info': 'remoteprobe',
      'favorite': 'false'}}
      Use this to get more information about any PRTG sensor if needed.'''
    context = get_prtg_data(user_input)
    return context

@function_tool
async def prtg_device_sensor_data(user_input:int)->str:
    '''You can get current information for all sensors that are down within a parent device ID. 
    Make sure to get integer sensor ID as input. Do not expect Device ID as input. Use the output to correlate with given alert and check for any systemic issues'''
    print(user_input)
    context = get_all_sensors_for_device(user_input)
    return context

@function_tool
async def child_sensors(user_input:int)->str:
    '''You can get current information for all child sensors that are down for the given sensor ID. 
    Make sure to get integer sensor ID as input. Use the output to correlate with given alert and check for any systemic issues'''
    print(user_input)
    context = get_all_downstream_sensors(user_input)
    return context

##Agents
ITSM_agent = Agent(name = 'ITSM_agent',
                  instructions =     
                   ''' You are an IT Service Management assistant designed to help 
                  Level 2 (L2) support engineers resolve user and system-generated tickets efficiently.
                  You only answer any IT related questions. 
                  Use sql_call to fetch any incidents or tickets data. 
                  Do not modify results of sql_call, just pass them as is.
                  Use pure_search to fetch any SOP, runbook, user manual data.
                  Ask users for a web search after you are done with pure_search. 
                  Always cite sources and links. Do not make up any information. 
                  If you don't know the answer, say "I don't know" .
                  Use tools unless you are absolutely sure you have all context.
                  Use web_search_call if user asks for a web search.
                  ''',
                   model=OpenAIResponsesModel(#OpenAIResponsesModel OpenAIChatCompletionsModel
                    model=openai_deployment,
                    openai_client=openai_client
                        ),
    tools=[Web_search_call, sql_call, pure_search] #pure_search rag_call
)

PRTG_agent = Agent(name = 'PRTG_agent',
                  instructions =     
                   ''' You are an IT agent specially designed for PRTG incidents and tickets.
                   You only answer PRTG related questions. Be friendly and polite. 
                   If you don't know the answer, just say "I don't know". Do not make up information
                   You will try to provide root cause analysis and ways to fix any PRTG ticket incident.
                   Provide scripts which can be executed without human intervention where possible.
                   Call prtg_sensor_data to get more information about current status of sensor. The incident would have been raised some time before. Make sure to render this data as a part of the answer if available. Determine if the sensor is currently up (statustext: Up) and use it as information to conclude that the issue is resolved.
                   Call web_search_call for internet search if needed.
                   If the user asks for a deeper search or is not satisfied with your resolution, call prtg_device_sensor_data. Use this output along with sensor data to provide a more detailed root cause, by evaluating reasons for other sensors of the device being down.
                   Call child_sensors to identify any downstream issues

                   Output format - Do not follow if user asks a follow-up question. Just use this for first resolution of a given incident
                   Summary of issue: Natural language interpretation of incident / user question
                   (Optional) Current state of sensor: show results of prtg_sensor_data in a table.  If available, show  prtg_device_sensor_data in a seperate table. Do not change any data here.
                   Root cause : Your understanding of why the issue is happening
                   Fix Approach : What actions should users take to remedy, including scripts to run. If the sensor is Up and issue is already fixed, make sure to highlight this and do not suggest fixes (if not required).
                   Downstream impact: If available, show output of child_sensors. Also summarize any issues you find and suggest possible fixes
                   Ask for web search or keep conversation on going.
                  ''',
                   model=OpenAIResponsesModel(#OpenAIResponsesModel OpenAIChatCompletionsModel
                    model=openai_deployment,
                    openai_client=openai_client
                        ),
    tools=[Web_search_call,prtg_sensor_data, prtg_device_sensor_data, child_sensors] #pure_search rag_call
)

#deprecated
sql_agent = Agent(name = 'SQL_agent',
                  instructions =     
                  '''You are a data generation tool designed to help pull RMS data for users.
                  You can take natural language inputs from user and convert to SQL query.
                  This is mainly tickets / incidents or service request data. 
                  Do not call for any generic questions. Do not change the output''',
                   model=OpenAIChatCompletionsModel(
                    model=openai_deployment,
                    openai_client=openai_client
                        ),
    tools=[sql_call] #rag_call, sql_call,
    
)

def handoff_message_filter(handoff_message_data: HandoffInputData) -> HandoffInputData:
    # Remove any tool-related messages from the message history
    handoff_message_data = handoff_filters.remove_all_tools(handoff_message_data)
    
    # Keep the full conversation history
    return handoff_message_data

## Entry point agent
customer_service_agent = Agent(
    name="Customer Service Agent",
    instructions=f'''{RECOMMENDED_PROMPT_PREFIX}.
    Your only purpose is to greet users and hold generic conversations.
    Don't try to solve the issue, just fetch relevant information.
    Hand-off IT related questions to ITSM agent.
    PRTG is a monitoring tool that can raise tickets / incidents if sensors or devices are not working.
    Hand-off PRTG related questions to PRTG agent. 
    Do not modify results or make up information.
    Be professional, friendly, and helpful. Be concise but show code, if available.
    Always cite your sources and provide links''',
    model=OpenAIChatCompletionsModel(# OpenAIResponsesModel OpenAIChatCompletionsModel
        model=openai_deployment,
        openai_client=openai_client
    ),
     handoffs=[handoff(ITSM_agent,input_filter=handoff_message_filter),
              handoff(PRTG_agent,input_filter=handoff_message_filter)],#, input_filter=handoff_message_filter
    #tools=[sql_call, Web_search_call]
)
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from openai import AzureOpenAI
from serpapi import GoogleSearch
from constants import openai_api_key , openai_api_version ,openai_endpoint,openai_deployment,openai_embedding_deployment,openai_search_service,openai_search_index,openai_search_key,openai_deployment_2,serp_api_key

top_results = 3 ##Move to parameters later
def search_vector_db(user_qry, top_results = 3):
    # Azure AI Search configuration
    search_service = openai_search_service
    index_name = openai_search_index
    search_key = openai_search_key
    embedding_deployment = openai_embedding_deployment

    ## Create Search Client for already created search service
    search_client = SearchClient(endpoint=f"https://{search_service}.search.windows.net",
    index_name=index_name,
    credential=AzureKeyCredential(search_key)
    )

    print(user_qry)
    vector = VectorizableTextQuery(text=user_qry, k_nearest_neighbors=50, fields="text_vector")
    results = search_client.search(search_text=user_qry,
        vector_queries=[vector],
        top=top_results)
    print('\n')
    print(results)

    return results

def search_qry_gen(user_qry, chat_history):

    # Azure OpenAI configuration
    openai_endpoint = openai_endpoint
    openai_key = openai_api_key
    chat_deployment = openai_deployment_2
    
    # Initialize clients
    openai_client = AzureOpenAI( api_key=openai_key,
        api_version= openai_api_version, ##"2025-03-15-preview", #"2024-12-01-preview",
        azure_endpoint=openai_endpoint
    )
    
    ## Generate history
    prompt_history = ''
    for item in chat_history:
        prompt_history+=item['role']
        prompt_history+=':\n'
        prompt_history+=item['content']
        prompt_history+=':\n\n'

    #Generate Prompt
    prompt = f'''
    system: 
    * Given the following conversation history and the users next question,rephrase the question to be a stand alone question.
    If the conversation is irrelevant or empty, just restate the original question.
    Do not add more details than necessary to the question.

    chat history:
    {prompt_history}
    
    Follow up Input: {user_qry}
    
    Standalone Question:
    '''

    result = openai_client.chat.completions.create(
         messages=[{'role': 'user', 'content': prompt}],
         max_completion_tokens=4096,
         model=chat_deployment
     )

    return result, prompt_history

def user_prompt_agg (search_results):
    # Compile retrieved documents
    documents = [f'''Content: {doc["chunk"]} \n,"source" : {doc['title']} \n''' for doc in search_results ]
    context = "\n\n".join(documents)

    return context

truncate_history = 15 #Parameterize later

def response_generator (user_qry, chat_history, truncate_history = 15):
    #print(user_qry, chat_history)
    search_qry, prompt_history = search_qry_gen(user_qry, chat_history)
    #print(search_qry)
    #print(prompt_history)
    search_results = search_vector_db(search_qry)
    #print(search_results)
    lookup_results = user_prompt_agg (search_results)
    #print(lookup_results)

    ## Explicit source Addition
    sources = [f'''{doc['title']}, ''' for doc in search_results ]
    sources = "\n\n".join(sources)
    sources = sources[:-2]

    # You are an IT Service Management assistant designed to help Level 2 (L2) support agents. Be respectful and polite.
    # You must reply with accuracy to inquirers' inquiries using only descriptors provided in that same context.
    # If there is ever a situation where you are unsure of the potential answers, simply respond with "I don't know".
    # Tailor responses to the specifics of the ticket or questions, adhering to accurate technical documentation, 
    # best practices, and logical troubleshooting steps. Always cite your source as available in context.
    
    final_prompt = f'''   
    context: {lookup_results}
    
    user: {user_qry}
    '''
    
    ##Create prompt with history
    messages = chat_history
    messages.append({'role': 'user', 'content': final_prompt})
    
    ##truncate_messages
    messages = messages[-15:]
    
    
    # Azure OpenAI configuration
    openai_key = openai_api_key
    chat_deployment = openai_deployment_2
    
    # Initialize clients
    openai_client = AzureOpenAI(
        api_key=openai_key,
        api_version= openai_api_version,
        azure_endpoint=openai_endpoint
    )
    
    #print(messages)
    result = openai_client.chat.completions.create(
         messages=messages,
         max_completion_tokens=4096,
         model=chat_deployment,
     )
    
    return result.choices[0].message.content

def  Web_search(user_qry : str) -> str:
    ''' Search the internet / web for results and more informaiton'''
    search = GoogleSearch({
        "q": user_qry, 
        "location": "Mumbai,India",
        "api_key": serp_api_key
      })
    result = search.get_dict()
    context = '\n'.join([i['snippet'] + f'''\n source is {i['link']} \n''' for i in result['organic_results']])
    
    return context




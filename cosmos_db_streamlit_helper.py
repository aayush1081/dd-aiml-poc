from streamlit import runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx
from azure.cosmos import CosmosClient, PartitionKey
from constants import cosmos_db_endpoint, cosmos_db_primary_key

def get_remote_ip() -> str:
    """Get remote ip."""

    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return None

        session_info = runtime.get_instance().get_client(ctx.session_id)
        if session_info is None:
            return None
    except Exception as e:
        return None

    return session_info.request.remote_ip


def create_cosmos_resources():
    # Initialize Cosmos DB client
    endpoint = cosmos_db_endpoint
    key = cosmos_db_primary_key
    #print(endpoint, key)
    client = CosmosClient(endpoint, key)
    print('created')
    # Database and container setup
    database_name = "chat_history"
    container_name = "v1_testing"
    # Create or get the database
    database = client.create_database_if_not_exists(id=database_name)
    # Create or get the container
    container = database.create_container_if_not_exists(
        id=container_name,
        partition_key=PartitionKey(path="/session_start"))
    
    return container
    
from secrets_loader import get_secret

# Load secrets once
openai_api_key = get_secret("AIML-POC-AZURE-OPENAI-API-KEY")
openai_api_version = get_secret("AIML-POC-AZURE-OPENAI-API-VERSION")
openai_endpoint = get_secret("AIML-POC-AZURE-OPENAI-ENDPOINT")
openai_deployment = get_secret("AIML-POC-AZURE-OPENAI-DEPLOYMENT")
openai_deployment_2 = get_secret("AIML-POC-AZURE-OPENAI-DEPLOYMENT2")
openai_embedding_deployment = get_secret("AIML-POC-AZURE-OPENAI-EMBEDDING-DEPLOYMENT")
openai_search_index = get_secret("AIML-POC-AZURE-SEARCH-INDEX")
openai_search_key = get_secret("AIML-POC-AZURE-SEARCH-KEY")
openai_search_service = get_secret("AIML-POC-AZURE-SEARCH-SERVICE")
cosmos_db_endpoint = get_secret("AIML-POC-COSMOS-DB-ENDPOINT")
cosmos_db_primary_key = get_secret("AIML-POC-COSMOS-DB-PRIMARY-KEY")
prtg_id = get_secret("AIML-POC-PRTG-ID")
prtg_pass = get_secret("AIML-POC-PRTG-PASS")
serp_api_key = get_secret("AIML-POC-SERP-API-KEY")

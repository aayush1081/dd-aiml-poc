from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient

tenant_id = '6180208d-4246-468f-9eee-53fb042edd91'
client_id = '2d48446d-3151-4525-9a8d-193619d4775a'
client_secret = 'KWW8Q~AtJJQ-~ofudWRjzGlW89YcWhITlnYszdgF'
vault_url = 'https://kv-aml-dd-001.vault.azure.net/'

# Authenticate
credential = ClientSecretCredential(tenant_id, client_id, client_secret)

# Create secret client
client = SecretClient(vault_url=vault_url, credential=credential)
def get_secret(secret_name):
    return client.get_secret(secret_name).value
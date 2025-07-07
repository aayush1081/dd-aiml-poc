import requests
import json
import time

def response_generator(user_prompt, history):
    endpoint_url = 'https://chatbot-trial-uxvtb.eastus2.inference.ml.azure.com/score'
    api_key = 'F17cETyRx4KSofgvaZlIa0Ra3rYA8EYO8d7x6jh8n10mh1swgfshJQQJ99BDAAAAAAAAAAAAINFRAZML4GoL'
    
    
    headers = {
        "Authorization": f"Bearer {api_key}","azureml-model-deployment": "chatbot-trial-uxvtb-2",
        "Content-Type": "application/json"} 

    payload = {
        "chat_input": {
         "history": [history],
          "question": user_prompt
        }
    }

    try:
        # Validate JSON first
        json.dumps(payload)
        
        response = requests.post(
            endpoint_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        # Even for errors, print the full response
        print(f"Status: {response.status_code}")
        #print("Response:", response.text)
        
        if response.status_code == 200:
            result = response.json()
            #return result
        else:
            result = "Error details:" + response.json()
    
    except json.JSONDecodeError as e:
        result = "Invalid JSON payload:" + e
    except requests.exceptions.RequestException as e:
        result = "Request failed:" + e

    print(result)
    
    for word in result['chat_output'].split():
        yield word + " "
        time.sleep(0.05)
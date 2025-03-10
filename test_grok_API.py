import requests
from dotenv import load_dotenv

load_dotenv()
import os
GROK_API_KEY = os.getenv('GROK_API_KEY')

# API endpoint
url = "https://api.x.ai/v1/chat/completions"

headers = {
    'Authorization': f'Bearer {GROK_API_KEY}',
    'Content-Type': 'application/json'
}

system_message_content = f"You are an domain expert"
user_message_content = f"Here is the text of a research paper:"
# User message
user_message = {
    "role": "user",
    "content": user_message_content
}

# System message
system_message = {
    "role": "system",
    "content": system_message_content
}

# Example payload for a POST request
data = {
    "messages": [system_message, user_message],
    'key': 'value',  # Adjust based on the API's expected input
    'model': "grok-2-latest",
    'stream': False,
    'temperature': 0
}

# Use POST if the endpoint requires it
response = requests.post(url, headers=headers, json=data)

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    try:
        data = response.json()
        print(data)
    except ValueError:
        print("Response is not valid JSON.")
else:
    print(f"Error: {response.status_code} - {response.text}")
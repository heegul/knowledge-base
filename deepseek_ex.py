import requests

# API endpoint and key
api_url = "https://api.deepseek.com/v1"
api_key = "sk-3bc4d19d3cc8409ea5b0c97d64004de3"

from openai import OpenAI

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "OK, upto October 2023, what are the major AI news?"},
    ],
    stream=False
)

print(response.choices[0].message.content)
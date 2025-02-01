import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

# Replace 'asst-abc123def456ghi789' with your custom model's ID
model_id = 'asst_fqPoDaMkUruEfi1P7ymJWpQc'

# Define the function parameters
function_name = "get_stock_price"
function_parameters = {
    "symbol": "AAPL"  # Example stock symbol for Apple Inc.
}

# Define the messages for the API call
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": f"Call function {function_name} with parameters {function_parameters}"}
]

# Call the OpenAI API
response = openai.ChatCompletion.create(
    model=model_id,  # Replace with your custom model ID
    messages=messages,
    functions=[{
        "name": function_name,
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "The stock symbol"
                }
            },
            "required": ["symbol"]
        },
        "description": "Get the current stock price"
    }],
    function_call="auto"  # This specifies that the function should be called automatically
)

# Extract the function result from the response
function_result = response['choices'][0]['message']['content']

# Print the result
print("Function Result:", function_result)

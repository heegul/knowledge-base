import json

# Load API keys from config.json
with open('config.json') as config_file:
    config = json.load(config_file)

OPENAI_API_KEY = config['OPENAI_API_KEY']
YOUTUBE_API_KEY = config['YOUTUBE_API_KEY']

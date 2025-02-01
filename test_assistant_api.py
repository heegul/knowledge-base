# Your API key here
from config import API_KEY 

# Your API key here
from config import OPENAI_API_KEY 

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

import openai
import webbrowser
import os
import re
import sys
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, NoTranscriptAvailable
from youtube_transcript_api.formatters import TextFormatter
from googleapiclient.discovery import build

openai.api_key = OPENAI_API_KEY
from typing_extensions import override  # Ensure you have this package installed
import openai

# Assuming you have the correct imports for OpenAI client, etc.
# Replace with actual correct imports if necessary
# from openai import AssistantEventHandler

# Define a class to handle events in the response stream
class EventHandler:  # Removed inheritance from non-existent AssistantEventHandler    
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)
      
    def on_text_delta(self, delta, snapshot):
        print(delta['value'], end="", flush=True)
      
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call['type']}\n", flush=True)
  
    def on_tool_call_delta(self, delta, snapshot):
        if delta['type'] == 'code_interpreter':
            if delta['code_interpreter']['input']:
                print(delta['code_interpreter']['input'], end="", flush=True)
            if delta['code_interpreter']['outputs']:
                print(f"\n\noutput >", flush=True)
                for output in delta['code_interpreter']['outputs']:
                    if output['type'] == "logs":
                        print(f"\n{output['logs']}", flush=True)

# Initialize OpenAI API client
openai.api_key = 'your-api-key'
client = openai.Client()

# Define your thread_id and assistant_id appropriately
thread_id = 'your-thread-id'
assistant_id = 'your-assistant-id'

# Use the `stream` SDK helper with the `EventHandler` class to create the Run 
# and stream the response.

with client.threads.runs.stream(
    thread_id=thread_id,
    assistant_id=assistant_id,
    instructions="Please address the user as Jane Doe. The user has a premium account.",
    event_handler=EventHandler(),
) as stream:
    stream.until_done()

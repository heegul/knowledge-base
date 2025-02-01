from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter


# Your API key here
from config import API_KEY 
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

import datetime
import pytz  # Importing pytz to ensure UTC is correctly handled

import openai

# Your API key here
from config import OPENAI_API_KEY 
openai.api_key = OPENAI_API_KEY


def full_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        formatter = TextFormatter()
        return formatter.format_transcript(transcript_list)
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

def check_transcript(video_id):
    try:
        YouTubeTranscriptApi.get_transcript(video_id)
        return True
    except Exception:
        return False

def youtube_search(query):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    try:
        search_response = youtube.search().list(
            q=query,
            part='id,snippet',
            maxResults=10,
            type='video',
            videoCaption='closedCaption',
            order='date'
        ).execute()

        video_details = []
        for item in search_response['items']:
            description = item['snippet']['description']
            enhanced_description = enhance_description(description)
            video_details.append((item['snippet']['title'], enhanced_description, f"https://www.youtube.com/watch?v={item['id']['videoId']}"))
        return video_details
    except Exception as e:
        print(f"Error during YouTube search: {e}")
        return []

def enhance_description(description):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": " You are a professional writer. Summarize this text."},
                  {"role": "user", "content": description}]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error enhancing description: {e}")
        return description

# Example usage
if __name__ == "__main__":
    summaries = youtube_search('Tesla latest news regarding stock price')
    for title, summary, url in summaries:
        print(f"Title: {title}\nDetailed Summary: {summary}\nURL: {url}\n")

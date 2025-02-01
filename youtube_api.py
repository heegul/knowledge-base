from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, NoTranscriptAvailable
from config import YOUTUBE_API_KEY
#from summary import get_summary
from summary_ollama import get_summary
from pdf_read import get_pdf_summary_claude, get_pdf_summary_lama3, get_pdf_summary_deepseek

def get_youtube_video_info(video_id, content_type='default'):
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()

        if 'items' in response and len(response['items']) > 0:
            video = response['items'][0]['snippet']
            title = video['title']
            description = get_transcript_summary(video_id, content_type)
            url = f"https://www.youtube.com/watch?v={video_id}"
            date = video['publishedAt']
            return title, description, url, video_id, date
        else:
            return None, None, None, None, None
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return None, None, None, None, None

def get_transcript_summary(video_id, content_type='default'):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = ' '.join([entry['text'] for entry in transcript_list])
        if content_type == 'claude':
            summary = get_pdf_summary_claude(full_text)
        elif content_type == 'lama3':
            summary = get_pdf_summary_lama3(full_text)
        elif content_type == 'deepseek':
            summary = get_pdf_summary_deepseek(full_text)
        else:
            summary = get_summary(full_text, content_type)

        return summary
    except (TranscriptsDisabled, NoTranscriptFound, NoTranscriptAvailable):
        return "Transcript not available."


# Your API key here
from config import API_KEY

# Your API key here
from config import OPENAI_API_KEY

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, NoTranscriptAvailable
from sentence_transformers import SentenceTransformer, util
import openai
import requests
import webbrowser
import os
import datetime



# Initialize the Sentence-Transformers model
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Initialize the OpenAI API
openai.api_key = OPENAI_API_KEY

def get_transcript_summary(video_id):
    try:
        # Fetch the transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Concatenate the transcript texts
        full_text = concatenate_transcript_texts(transcript_list)
        
        # Get summary from OpenAI API
        summary = get_summary(full_text)
        
        # Include relevant start values
        summary_with_times = include_relevant_start_values(video_id, transcript_list, summary)
        
        # Format the result as HTML
        formatted_summary = format_summary(summary_with_times)
        
        return formatted_summary
    
    except TranscriptsDisabled:
        return "Transcripts are disabled for this video."
    except NoTranscriptFound:
        return "No transcript found for this video."
    except NoTranscriptAvailable:
        return "No transcript available in the requested languages."

def concatenate_transcript_texts(transcript_list):
    return " ".join([entry['text'] for entry in transcript_list])

def get_summary(text):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system", 
                "content": (
                "You are an expert in the technical domain relevant to the topic being discussed in the video. "
                "Assume the audience is also made up of domain experts. Summarize this text to deliver the main ideas, "
                "highlight key technical insights, elaborate on important points, and provide deep, nuanced analysis. "
                "Ensure the summary is comprehensive and detailed, capturing the essence of the discussion."
            )},
            {"role": "user", "content": text}
        ]
    )
    return response['choices'][0]['message']['content'].strip()

def include_relevant_start_values(video_id, transcript_list, summary):
    # Split summary into lines
    summary_lines = summary.split('\n')
    
    # Create a list of transcript texts and their start times
    transcript_texts = [entry['text'] for entry in transcript_list]
    start_times = [entry['start'] for entry in transcript_list]
    
    # Compute embeddings for transcript texts and summary lines
    transcript_embeddings = model.encode(transcript_texts, convert_to_tensor=True)
    summary_embeddings = model.encode(summary_lines, convert_to_tensor=True)
    
    summary_with_start_times = []
    
    for summary_line, summary_embedding in zip(summary_lines, summary_embeddings):
        # Compute cosine similarities
        similarities = util.pytorch_cos_sim(summary_embedding, transcript_embeddings)[0]
        
        # Find the index of the most similar transcript entry
        best_match_index = similarities.argmax()
        
        # Get the start time of the best match
        best_match_start_time = start_times[best_match_index]
        
        # Create a YouTube link with a timestamp
        youtube_link = f"https://www.youtube.com/watch?v={video_id}&t={int(best_match_start_time)}s"
        
        # Append the summary line with the start time as a hyperlink
        summary_with_start_times.append(f"{summary_line} (<a href='{youtube_link}' target='_blank'>Start: {best_match_start_time:.2f}s</a>)")
    
    return summary_with_start_times

def format_summary(summary_with_times):
    formatted_list_items = ''.join(f'<li>{item}</li>' for item in summary_with_times)
    return f'<ul>{formatted_list_items}</ul>'

def generate_html_from_summary(title, url, formatted_summary):
    """
    Generate a structured HTML content block from a formatted summary string, incorporating enhanced CSS styles.
    """
    # Building the HTML content with embedded CSS for better styling
    html_content = f'''
    <div class="article-summary">
        <h2><a href="{url}" target="_blank">{title}</a></h2>
        <ul class="summary-list">{formatted_summary}</ul>
    </div>
    '''
    return html_content
html_header = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Summaries</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f4f4f4;
            color: #333;
        }
        .container {
            width: 80%;
            margin: auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px 0 rgba(0,0,0,0.1);
        }
        h1 {
            color: #444;
        }
        h2 {
            font-size: 18px;
            color: #065a82;
        }
        ul, li {
            padding: 0;
            list-style-type: none;
        }
        li {
            margin-bottom: 10px;
            font-size: 16px;
            color: #666;
            line-height: 1.5;
        }
        .subtitle {
            font-weight: bold;
        }
        a {
            color: #0645ad;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>YouTube Video Summaries</h1>
'''


def create_html_page(video_id, filename):
    html_content = html_header
    formatted_summary = get_transcript_summary(video_id)
    html_content += formatted_summary
    #print(formatted_summary)
    #formatted_summary_str = format_summary(summary)
    #html_content += generate_html_from_summary(title,url,formatted_summary_str)
        

    html_content += '''
    </div>
</body>
</html>
'''
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)

    webbrowser.open('file://' + os.path.realpath(filename))



# Example usage
#video_id = "dWZyXRBYQ-Y"
#video_id = "UPtG_38Oq8o" 
video_id = "fKMB5UlVY1E"

create_html_page(video_id, 'Attention_Transformer_test.html')

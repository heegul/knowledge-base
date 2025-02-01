
# Your API key here
from config import API_KEY 

# Your API key here
from config import OPENAI_API_KEY 

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

import openai
from openai import Completion
import webbrowser
import os
import re
import sys
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, NoTranscriptAvailable
from youtube_transcript_api.formatters import TextFormatter
from googleapiclient.discovery import build
from sentence_transformers import SentenceTransformer, util


# Initialize the Sentence-Transformers model
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')


openai.api_key = OPENAI_API_KEY

def fetch_transcript(video_id):
    try:
        # Fetch the transcript for the given video ID
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        for entry in transcript:
            print(f"{entry['start']} - {entry['duration']}: {entry['text']}")
    except TranscriptsDisabled:
        print("Transcripts are disabled for this video.")
    except NoTranscriptFound:
        print("No transcript found for this video.")
    except NoTranscriptAvailable:
        print("No transcript available in the requested languages.")

def list_available_transcripts(video_id):
    try:
        # List all available transcripts for the given video ID
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in transcripts:
            print(f"Language: {transcript.language} (Generated: {transcript.is_generated})")
    except TranscriptsDisabled:
        print("Transcripts are disabled for this video.")
    except NoTranscriptFound:
        print("No transcript found for this video.")

def find_text_in_transcript(video_id, search_text):
    try:
        # Fetch the transcript for the given video ID
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Search for the text in the transcript
        for entry in transcript:
            if search_text.lower() in entry['text'].lower():
                start_time = entry['start']
                return generate_youtube_link(video_id, start_time)
        
        # If the text is not found
        return f"Text '{search_text}' not found in the transcript."
    
    except TranscriptsDisabled:
        return "Transcripts are disabled for this video."
    except NoTranscriptFound:
        return "No transcript found for this video."
    except NoTranscriptAvailable:
        return "No transcript available in the requested languages."

def generate_youtube_link(video_id, start_time):
    # Convert start time (in seconds) to a YouTube URL with a timestamp
    return f"https://www.youtube.com/watch?v={video_id}&t={int(start_time)}s"

def enhance_description(description, role):
    if role == 'writer':
        role_string = " You are a professional writer. Summarize this text with at least 3 bullet points."
    elif role =='teacher' or role == 'professor':
        role_string = " You are a professional professor. Summarize this text with at least 3 bullet points for graduate students to understand easily."
    elif role == 'researcher':
        role_string = "You are a expert in a certain domain relavant to the topic being discussed. Assume listeners are also domain experts so elaborate and summarize this text to deliver the main ideas."
    else:
        role_string = "summarize this text"
        
    try:
        response = openai.ChatCompletion.create(
            #model="gpt-4-turbo",
            model="gpt-4o",
            messages=[{"role": "system", "content": role_string},
                  {"role": "user", "content": description}]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error enhancing description: {e}")
        return description
def get_transcript(video_id):
    preferred_languages = ['en', 'en-US','kr']
    try:
        # Fetching the transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=preferred_languages)
        #transcript = transcript_list.find_transcript(['en'])

        # Format the transcript into plain text
        formatter = TextFormatter()
        transcript_text = formatter.format_transcript(transcript_list)
        in_string = transcript_text.replace(".\n", ". ")
        out_string = in_string.replace("\n", ". ")
        return out_string

    except Exception as e:
        print("An error occurred while fetching the transcript:", str(e))

def generate_html_from_summary(title, url, formatted_summary_str):
    """
    Generate a structured HTML content block from a formatted summary string,
    incorporating enhanced CSS styles, and treating lines starting with '- **Title**:'
    as subsection headers within the list.
    """
    # Pattern to find subtitles and content
    pattern = re.compile(r'- \*\*([^*]+)\*\*:(.*)')
    items = []

    for line in formatted_summary_str.split('\n'):
        match = pattern.match(line)
        if match:
            subtitle, content = match.groups()
            items.append(f'<li class="summary-item"><strong>{subtitle.strip()}:</strong> {content.strip()}</li>')
        elif line.strip():  # Handle lines that are not empty and do not match the pattern
            items.append(f'<li class="summary-item">{line.strip()}</li>')

    formatted_list_items = ''.join(items)

    html_content = f'''
    <div class="article-summary">
        <h2><a href="{url}" target="_blank">{title}</a></h2>
        <ul class="summary-list">{formatted_list_items}</ul>
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


def create_html_page(summaries, filename):
    html_content = html_header
    for title, summary, url in summaries:
        #print(summary)
        formatted_summary_str = format_summary(summary)
        html_content += generate_html_from_summary(title,url,formatted_summary_str)
        

    html_content += '''
    </div>
</body>
</html>
'''
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)

    webbrowser.open('file://' + os.path.realpath(filename))

def format_summary(summary):
    # Splitting summary based on your specified pattern to find subtitles and content
    pattern = re.compile(r' - \*\*([^*]+)\*\*:')
    list_items = ''
    start = 0
    if summary is not None:
        for match in pattern.finditer(summary):
            title = match.group(1).strip()
            end = match.start()
            content = summary[start:end].strip()
            if content:
                list_items += f'<li>{content}</li>'
            list_items += f'<li class="subtitle">{title}:</li>'
            start = match.end()

        # Add any remaining content after the last subtitle as a bullet point
        if start < len(summary):
            content = summary[start:].strip()
            list_items += f'<li>{content}</li>'

    return list_items


def chat_about_video(video_title, video_id, initial_summary):
    print(f"Summary of the video '{video_title}':\n{initial_summary}")
    print("\nYou can now chat about the video. Type 'exit' to end the chat.")
    
    # Initialize the chat messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Video Title: {video_title}"},
        {"role": "user", "content": f"Summary: {initial_summary}"}
    ]


    html_content = html_header
    while True:
        user_input = input("You: ")
        html_content += user_input+ '<br>'
        
        if user_input.lower() == 'exit':
            break
        
        # Add user input to messages
        messages.append({"role": "user", "content": user_input})
        
        # Send the conversation to ChatGPT
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages
        )
        
        answer = response['choices'][0]['message']['content']
        #print(f"ChatGPT: {answer}")
        formatted_answer_str = format_summary(answer)
        url =  f"https://www.youtube.com/watch?v={video_id}"
        html_content += generate_html_from_summary(video_title,url,formatted_answer_str)
        
        # Append ChatGPT's response to the messages
        messages.append({"role": "assistant", "content": answer})
        #html_content += f"ChatGPT: {answer}"



    html_content += '''

    </div>
</body>
</html>
'''
    filename = f'{video_title}+{video_id}.html'
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)

    webbrowser.open('file://' + os.path.realpath(filename))






if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python script_name.py <youtube:video_id> <youtube:video_id> ,,,")
        sys.exit(1)

    search_query = sys.argv[1]  # Join all arguments to form the query



# Example usage
#video_id = ['dWZyXRBYQ-Y']

video_id = []
for id in range(len(sys.argv)-1):
    video_id.append(sys.argv[id+1])

#fetch_transcript(video_id)
#list_available_transcripts(video_id)
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

summaries =[]
for video in video_id:
    out_string = get_transcript(video)
    summary = enhance_description(out_string,'researcher')
    #summary = "Dr. Melike Erol-Kantarci, an esteemed expert in AI and next-generation wireless networks, presented a comprehensive seminar on the role and applications of AI techniques in 5G and 6G networks, focusing particularly on reinforcement learning and deep reinforcement learning. Here are the key points and insights shared in her detailed presentation:\n\n1. **Speaker's Background:**\n   - Dr. Erol-Kantarci is a leading figure in AI-enabled wireless networks, holding significant roles at Ericsson and the University of Ottawa. She has a substantial body of work with over 150 peer-reviewed publications.\n\n2. **Need for AI in Wireless Networks:**\n   - The pressing need for improved automation and performance in wireless networks is driven by increasing complexity due to spectrum limitations, the rise of millimeter waves, massive multiple-input multiple-output (MIMO) systems, mobile edge computing, virtualized RANs, and network slicing.\n\n3. **Reinforcement Learning (RL) in Wireless Networks:**\n   - Dr. Erol-Kantarci explained the fundamentals of reinforcement learning, including its basis in Markov Decision Processes (MDPs). She emphasized trial and error as essential for learning policies that maximize rewards.\n   - For model-free environments common in wireless networks, Q-learning (a type of RL) is useful but can struggle with large state-action spaces and continuous states.\n\n4. **Deep Reinforcement Learning (DRL):**\n   - Combines RL with deep learning to approximate Q-values for complex environments. Techniques like target deep networks and experience replay memory stabilize learning and improve convergence.\n\n5. **Transfer Learning and Transfer Reinforcement Learning (TRL):**\n   - Transfer learning harnesses knowledge from previously learned tasks to accelerate learning in new but related tasks. TRL can enhance wireless network functions by transferring optimized policies from expert nodes to learner nodes, reducing training time significantly.\n\n6. **Applications and Research Findings:**\n   - The presented research included innovative solutions like using DBSCAN (a clustering technique) and DRL for resource allocation in 5G networks, showing significant improvements in latency and throughput.\n   - Another presented study addressed carrier aggregation in 5G, balancing resource allocation to optimize UE (user equipment) energy consumption.\n\n7. **Layered Applications of TRL in RAN Slicing:**\n   - Dr. Erol-Kantarci shared how TRL was applied to RAN slicing, optimizing between URLLC (ultra-reliable low latency communications) and eMBB (enhanced mobile broadband) slices for both latency and throughput.\n\n8. **Team Learning in ORAN:**\n   - Focused on the O-RAN alliance's innovative architecture promoting multi-vendor interactions. Dr. Erol-Kantarci introduced a team learning approach where collaborative RL agents share actions to align and optimize their joint policies, demonstrating superior performance over independent learning.\n\n9. **Future of AI in Wireless Networks:**\n   - She concluded by emphasizing the ongoing AI spring in wireless networks, recognizing both opportunities and challenges in scalability, convergence, and data standardization. AI ensures optimized network management while considering energy efficiency, security, and latency.\n\n10. **Engagement and Further Exploration:**\n    - Dr. Erol-Kantarci invited questions and shared her enthusiasm for federated learning as another promising AI technique for wireless networks, underscoring the potential for AI to revolutionize this critical infrastructure.\n\nIn sum, the presentation highlighted the transformative potential of AI and machine learning in enhancing the efficiency, reliability, and performance of next-generation wireless networks, underscoring ongoing research efforts and future directions."
    # Request to get video details
    request = youtube.videos().list(
        part='snippet',
        id=video
    )

    # Execute the request
    response = request.execute()

    # Extract the video title from the response
    # Check if the response contains items
    if not response['items']:
        print(f"No video found for ID: {video}")
    else:
        # Extract the video title from the response
        video_title = response['items'][0]['snippet']['title']
        video_url = f"https://www.youtube.com/watch?v={video}"

    summaries.append((video_title,summary,video_url))
    create_html_page(summaries,f'{video}_summary.html')

    chat_about_video(video_title,video, summary)




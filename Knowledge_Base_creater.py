import sqlite3
import json
import sys

# Your API key here
from config import API_KEY 

# Your API key here
from config import OPENAI_API_KEY 

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, NoTranscriptAvailable
from sentence_transformers import SentenceTransformer, util
import openai
# import requests
# import webbrowser
# import os
# import datetime
from googleapiclient.discovery import build

# Initialize the OpenAI API
openai.api_key = OPENAI_API_KEY


def get_youtube_video_info(video_id):
    # Initialize the YouTube API client
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    
    # Fetch video details
    request = youtube.videos().list(
        part="snippet",
        id=video_id
    )
    response = request.execute()

    # Extract video information
    if 'items' in response and len(response['items']) > 0:
        video = response['items'][0]['snippet']
        title = video['title']
        description = get_transcript_summary(video_id)
        url = f"https://www.youtube.com/watch?v={video_id}"
        date = video['publishedAt']
        channel_id = video['channelId']

        return (title, description, url, video_id, date, channel_id)
    else:
        return None
    

# Function to create a connection to the SQLite database
def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

def check_table_exists(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if cursor.fetchone()[0] == 1:
        return True
    return False


# Function to create tables
def create_tables(conn):
    try:
        cursor = conn.cursor()
        
        # Create Sources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Sources (
                source_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT,
                url TEXT,
                author TEXT,
                publication_date DATE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Videos (
                video_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT NOT NULL,
                publication_date DATE,
                channel_id INTEGER,
                topic_id INTEGER,
                summary TEXT,
                FOREIGN KEY (channel_id) REFERENCES Channels (channel_id),
                FOREIGN KEY (topic_id) REFERENCES Topics (topic_id)
            )
        ''')

        # Create Topics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Topics (
                topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT
            )
        ''')

        # Create Articles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Articles (
                article_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                abstract TEXT,
                content TEXT,
                publication_date DATE,
                source_id INTEGER,
                topic_id INTEGER,
                FOREIGN KEY (source_id) REFERENCES Sources (source_id),
                FOREIGN KEY (topic_id) REFERENCES Topics (topic_id)
            )
        ''')

        # Create Experts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Experts (
                expert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                affiliation TEXT,
                bio TEXT,
                fields TEXT,
                contact_info TEXT
            )
        ''')

        # Create Events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date DATE,
                location TEXT,
                description TEXT,
                url TEXT
            )
        ''')

        # Create Courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Courses (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                provider TEXT,
                description TEXT,
                url TEXT,
                start_date DATE,
                end_date DATE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_clips (
                title TEXT NOT NULL,
                description TEXT,
                url TEXT,
                video_id TEXT,
                date DATE,
                channel_id TEXT
            )
        ''')
        
        conn.commit()
    except Exception as e:
        print(e)

# Function to insert sample data
def insert_sample_data(conn):
    cursor = conn.cursor()

    # Insert sample sources
    sources = [
        ("AI Research Journal", "Journal", "https://ai-journal.com", "John Doe", "2024-01-15"),
        ("AI News Daily", "News", "https://ainewsdaily.com", "Jane Smith", "2024-05-10"),
        ("YouTube AI Channel", "YouTube", "https://youtube.com/AIChannel", "Tech Guru", "2024-03-20")
    ]
    cursor.executemany('''
        INSERT INTO Sources (name, type, url, author, publication_date)
        VALUES (?, ?, ?, ?, ?)
    ''', sources)

    # Insert sample topics
    topics = [
        ("Machine Learning", "The study of algorithms that improve automatically through experience."),
        ("Neural Networks", "A subset of machine learning involving algorithms inspired by the structure of the human brain."),
        ("Natural Language Processing", "The field focused on the interaction between computers and humans through natural language."),
        ("Semantic Communications", "The field focused on communications all the way in which one mind may affect another in desired way")
    ]
    cursor.executemany('''
        INSERT INTO Topics (name, description)
        VALUES (?, ?)
    ''', topics)

    # Insert sample articles
    articles = [
        ("Introduction to Machine Learning", "An overview of machine learning techniques.", "Full content of the article goes here.", "2024-01-20", 1, 1),
        ("Advances in Neural Networks", "Latest research in neural networks.", "Full content of the article goes here.", "2024-03-15", 1, 2),
        ("NLP for Beginners", "Introduction to Natural Language Processing.", "Full content of the article goes here.", "2024-02-10", 2, 3),
        ("Semantic communication", "Introduction to Natural Language Processing.", "Full content of the article goes here.", "2024-02-10", 1, 4)
    ]
    cursor.executemany('''
        INSERT INTO Articles (title, abstract, content, publication_date, source_id, topic_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', articles)

    # Insert sample experts
    experts = [
        ("Andrew Ng", "Stanford University", "Pioneer in machine learning and online education.", "Machine Learning, AI", "andrew.ng@stanford.edu"),
        ("Yoshua Bengio", "University of Montreal", "Renowned for his work on deep learning.", "Deep Learning, Neural Networks", "yoshua.bengio@umontreal.ca")
    ]
    cursor.executemany('''
        INSERT INTO Experts (name, affiliation, bio, fields, contact_info)
        VALUES (?, ?, ?, ?, ?)
    ''', experts)

    # Insert sample events
    events = [
        ("AI Conference 2024", "2024-08-15", "San Francisco, CA", "Annual conference on AI advancements.", "https://aiconference2024.com"),
        ("NLP Workshop", "2024-09-10", "New York, NY", "Workshop on Natural Language Processing.", "https://nlpworkshop2024.com")
    ]
    cursor.executemany('''
        INSERT INTO Events (name, date, location, description, url)
        VALUES (?, ?, ?, ?, ?)
    ''', events)

    # Insert sample courses
    courses = [
        ("Machine Learning by Andrew Ng", "Coursera", "Comprehensive course on machine learning.", "https://coursera.org/ml-course", "2024-06-01", "2024-12-01"),
        ("Deep Learning Specialization", "Coursera", "Series of courses on deep learning.", "https://coursera.org/deep-learning", "2024-07-01", "2024-12-31")
    ]
    cursor.executemany('''
        INSERT INTO Courses (name, provider, description, url, start_date, end_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', courses)

    conn.commit()

# Function to query data
def query_data(conn):
    cursor = conn.cursor()

    # Example query: Get all articles on a specific topic
    topic_id = 4
    cursor.execute('''
        SELECT title, abstract, publication_date FROM Articles WHERE topic_id = ?
    ''', (topic_id,))
    articles = cursor.fetchall()
    print("Articles on Topic ID 1:")
    for article in articles:
        print(article)

    # Example query: List all upcoming events
    cursor.execute('''
        SELECT name, date, location, description FROM Events WHERE date >= DATE('now')
    ''')
    events = cursor.fetchall()
    print("\nUpcoming Events:")
    for event in events:
        print(event)

    # Example query: Get information about a specific expert
    expert_id = 1
    cursor.execute('''
        SELECT name, affiliation, bio, fields, contact_info FROM Experts WHERE expert_id = ?
    ''', (expert_id,))
    expert = cursor.fetchone()
    print("\nInformation about Expert ID 1:")
    print(expert)

def query_youtube_data(conn,video_id):
    cursor = conn.cursor()

    # Example query: Get all articles on a specific topic

    cursor.execute('''
        SELECT title, description, url, video_id, date, channel_id FROM video_clips WHERE video_id = ?
    ''', (video_id,))
    video_clips = cursor.fetchall()
    print(f"Articles on Video ID {video_id}:")
    for video in video_clips:
        print(video)

# Function to query data and save as JSON
def query_youtube_data_to_json(conn,video_id):
    cursor = conn.cursor()
    
    # Query articles
    # cursor.execute('''
    #     SELECT a.title, a.description, a.url, a.video_id, a.date, a.channel_id
    #     FROM video_clips a WHERE video_id = ?
    # ''', (video_id,))
    cursor.execute('''
        SELECT a.title, a.description, a.url, a.video_id, a.date, a.channel_id
        FROM video_clips a
    ''')
    articles = cursor.fetchall()
    
    # Convert articles to dictionary
    articles_list = []
    for article in articles:
        articles_list.append({
            "title": article[0],
            "description": article[1],
            "url": article[2],
            "video_id": article[3],
            "date": article[4] ,
            "channel_id":article[5]
        })
    
    # Save articles to JSON file
    with open('articles.json', 'w') as json_file:
        json.dump({"articles": articles_list}, json_file, indent=4)
    
    print("Data saved to articles.json")




def insert_youtube_article(conn,  video_clip):
    cursor = conn.cursor()
    # video_clips = [
    #     ("Machine Learning by Andrew Ng", "Coursera", "Comprehensive course on machine learning.", "https://coursera.org/ml-course", "2024-06-01", "2024-12-01"),
    #     ("Deep Learning Specialization", "Coursera", "Series of courses on deep learning.", "https://coursera.org/deep-learning", "2024-07-01", "2024-12-31")
    # ]
    cursor.executemany('''
        INSERT INTO video_clips (title, description, url, video_id, date, channel_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', video_clip)

    conn.commit() 

def concatenate_transcript_texts(transcript_list):
    return " ".join([entry['text'] for entry in transcript_list])

# def format_description(description):
#     # Split the description into paragraphs and lines for processing
#     paragraphs = description.split('\n\n')

#     # Initialize an empty string for the formatted HTML
#     formatted_html = ""

#     for paragraph in paragraphs:
#         if paragraph.startswith("### "):
#             # If the paragraph starts with "### ", it's a heading
#             heading_text = paragraph[4:].strip()
#             formatted_html += f"<h3>{heading_text}</h3>\n"
#         elif paragraph.startswith("- "):
#             # If the paragraph starts with "- ", it's a list
#             list_items = paragraph.split('\n- ')
#             formatted_html += "<ul>\n"
#             for item in list_items:
#                 if item:
#                     formatted_html += f"    <li>{item.strip()}</li>\n"
#             formatted_html += "</ul>\n"
#         else:
#             # Otherwise, it's a normal paragraph
#             formatted_html += f"<p>{paragraph.strip()}</p>\n"

#     return formatted_html

import re

def format_description(description):
    # Convert Markdown-like headers to HTML headers
    description = re.sub(r'### (.*?)\n', r'<h3>\1</h3>\n', description)
    
    # Convert Markdown-like bold text to HTML bold
    description = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', description)
    
    # Convert Markdown-like lists to HTML lists
    description = re.sub(r'\n- ', r'<li>', description)
    description = re.sub(r'\n(?=[^<li>])', r'</li>\n', description)
    description = re.sub(r'</li>\n<li>', r'\n<li>', description)
    description = re.sub(r'<li>', r'<ul>\n<li>', description, count=1)
    description += '</li>\n</ul>' if '<li>' in description else ''
    
    # Wrap paragraphs with <p> and </p>
    paragraphs = description.split('\n\n')
    formatted_html = "".join([f"<p>{p.strip()}</p>" if not p.strip().startswith('<h3>') and not p.strip().startswith('<ul>') else p for p in paragraphs])

    return formatted_html


def get_transcript_summary(video_id):
    try:
        # Fetch the transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Concatenate the transcript texts
        full_text = concatenate_transcript_texts(transcript_list)
        # Get summary from OpenAI API
        description = get_summary(full_text)
        description = description.replace('\n','<br>')
        f_description = format_description(description)


        return f_description
        
    except TranscriptsDisabled:
        return "Transcripts are disabled for this video."
    except NoTranscriptFound:
        return "No transcript found for this video."
    except NoTranscriptAvailable:
        return "No transcript available in the requested languages."
           
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


# Main execution
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <youtube:video_clip>")
        sys.exit(1)

    video_id = sys.argv[1]  # Join all arguments to form the query

    conn = create_connection('knowledge_base.db')
    if not check_table_exists(conn, 'video_clips'):
    #if True:
        create_tables(conn)
        insert_sample_data(conn)
    
    #video_id = "fKMB5UlVY1E"
    video_clip =[]
    video_clip.append(get_youtube_video_info(video_id))

    insert_youtube_article(conn,video_clip)
    query_youtube_data(conn,video_id)
    query_youtube_data_to_json(conn,video_id)
    conn.close()

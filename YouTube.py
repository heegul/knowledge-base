from dotenv import load_dotenv
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter


import os

load_dotenv()

API_KEY = os.getenv('YOUTUBE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
BING_SEARCH_API = os.getenv('BING_SEARCH_API')


YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

import logging
logging.basicConfig(level=logging.INFO)

import argparse

try:
    from newsapi import NewsApiClient
    print("newsapi-python is installed and imported successfully.")
except ModuleNotFoundError:
    print("newsapi-python is not installed.")


from azure.cognitiveservices.search.newssearch import NewsSearchClient

from msrest.authentication import CognitiveServicesCredentials
from bs4 import BeautifulSoup

# Initialize the client with your API key.
newsapi = NewsApiClient(api_key=NEWS_API_KEY)
import logging
import httplib2
import requests
import re
endpoint = "https://api.bing.microsoft.com/v7.0/news/search"
credentials = CognitiveServicesCredentials(BING_SEARCH_API)
client_bing = NewsSearchClient(endpoint=endpoint, credentials=credentials)





import openai
from googleapiclient.discovery import build
from openai import Completion

import webbrowser
import os
import sys  # Import sys to handle command line arguments
import re
import datetime
import pytz  # For timezone conversions
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.formatters import TextFormatter


YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

openai.api_key = OPENAI_API_KEY


def youtube_search(query, role):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    print(youtube)

    # Get current UTC time and compute the time 24 hours ago
    now = datetime.datetime.utcnow()  # Ensuring we're using UTC
    #now = datetime.datetime.now(datetime.UTC)
    one_day_ago = now - datetime.timedelta(days=1)
    two_day_ago = now - datetime.timedelta(days=2)
    one_day_ago_iso = two_day_ago.replace(microsecond=0).isoformat() + "Z"  # Ensure no timezone info, just 'Z'

    try:
        # Use the correctly formatted timestamp in the API call
        if role=='writer':
            #analyst_names = ["Adam Jonas", "Dan Ives", "Cathie Wood"]  # List of prominent analysts
            #query += ". " + " OR ".join(analyst_names)
            print(query)
            search_response = youtube.search().list(
                q=query,
                part='id,snippet',
                maxResults=10,
                type='video',
                videoCaption='closedCaption',
                publishedAfter=one_day_ago_iso
            ).execute()
        else:
            search_response = youtube.search().list(
                q=query,
                part='id,snippet',
                maxResults=10,
                type='video',
                videoCaption='closedCaption',
            ).execute()

        # Filter further by channel subscriber count
        filtered_videos = []
        for item in search_response['items']:
            channel_id = item['snippet']['channelId']
            channel_response = youtube.channels().list(
                id=channel_id,
                part='statistics',
                fields='items/statistics/subscriberCount'
            ).execute()

            if channel_response['items']:
                subscriber_count = int(channel_response['items'][0]['statistics']['subscriberCount'])
                if role == 'writer':
                    sub_thr=1000
                else:
                    sub_thr=500

                if subscriber_count > sub_thr:
                    filtered_videos.append(item)

        # Process filtered videos for summary
        summaries = []
        for video in filtered_videos:
            description = video['snippet']['description']
            title = video['snippet']['title']
            video_id = video['id']['videoId']
            #print(video_id)
            preferred_languages = ['en', 'en-US']
            try:
                # Fetching the transcript
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=preferred_languages)
                #transcript = transcript_list.find_transcript(['en'])

                # Format the transcript into plain text
                formatter = TextFormatter()
                transcript_text = formatter.format_transcript(transcript_list)
            except Exception as e:
                print("An error occurred while fetching the transcript:", str(e))

            summary = enhance_description_llama(transcript_text, role)
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            summaries.append((title, summary, video_url))

        return summaries

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def enhance_description(description, role):
    if role == 'writer':
        role_string = " You are a professional writer. Summarize this text with at least 10 bullet points."
    elif role =='teacher' or role == 'professor' or role == 'researcher':
        role_string = " You are a expert in a certain domain relavant to the topic being discussed. Assume listeners are also domain experts so elaborate and summarize this text to deliver the main ideas."
    else:
        role_string = "summarize this text"
        
    try:
        response = openai.ChatCompletion.create(
            #model="gpt-4o",
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "system", "content": role_string},
                  {"role": "user", "content": description}]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error enhancing description: {e}")
        return description

def enhance_description_llama(description, role):
    # Define the role-specific instructions
    role_instructions = {
        'writer': "You are a professional writer. Summarize this text. Assume listeners are also domain experts so elaborate and summarize this text to deliver the main ideas.",
        'expert': "You are an expert in a certain domain relevant to the topic being discussed. Assume listeners are also domain experts so elaborate and summarize this text to deliver the main ideas. itemize it with bullet points under subitems. make content amount be one page of summary.",
        'professor': "You are an expert in a certain domain relevant to the topic being discussed. Assume listeners are also domain experts so elaborate and summarize this text to deliver the main ideas.",
        'researcher': "You are an expert in a certain domain relevant to the topic being discussed. Assume listeners are also domain experts so elaborate and summarize this text to deliver the main ideas.",
    }

    # Get the role-specific instruction or use a default
    role_string = role_instructions.get(role, "Summarize this text")

    role_string += ' IGNORE HTML code AND FOCUS ON CONTENT!'

    # Create the Ollama instance with llama3 model
    llm = Ollama(model="llama3")

    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", role_string),
        ("human", "{description}")
    ])

    # Create the chain
    chain = prompt | llm | StrOutputParser()

    try:
        # Invoke the chain
        result = chain.invoke({"description": description})
        return result.strip()
    except Exception as e:
        print(f"Error enhancing description: {e}")
        return description

def summarize_text(text):
    response = openai.ChatCompletion.create(
        model="text-embedding-3-large",
        messages=[{"role": "system", "content": " You are a professional stock analyst. Summarize the following text at least 3 lines with at least 4 bullet points. And provide me with sentimental score out of 10. i.e. if positive, give 10. you can search more for the internet finantial news if you need to find out supporting factors."},
                  {"role": "user", "content": text}]
    )
    return response['choices'][0]['message']['content'].strip()



def search_news(query, role):
    today = datetime.date.today()
    two_days_ago = today - datetime.timedelta(days=2)

    try:
        all_articles = newsapi.get_everything(
            q=query,
            language='en',
            sort_by='publishedAt',
            from_param=two_days_ago.isoformat(),
            to=today.isoformat(),
            page_size=10
        )
        summaries = []
        for article in all_articles['articles']:
            summary = enhance_description_llama(article['description'], role)
            summaries.append((article['title'], summary, article['url']))

        return summaries
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

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



def create_html_page(summaries, filename):
    html_content = '''
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
        <h1>Articles and Video Summaries</h1>
'''
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
    
def test_youtube_api():
    try:
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
        request = youtube.videos().list(part="snippet", chart="mostPopular", regionCode="US", maxResults=5)
        response = request.execute()
        print(response)
        return True
    except Exception as e:
        print(f"Failed to query YouTube API: {e}")
        return False

def get_full_article_content_draft(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch article. Status code: {response.status_code}")
        return None


def get_full_article_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        article_content = []

        # Function to extract text from elements
        def extract_text(elements):
            for element in elements:
                text = element.get_text(separator=' ', strip=True)
                if text:
                    article_content.append(text)

                # Extract text from nested spans and links within these elements
                spans = element.find_all('span')
                for span in spans:
                    span_text = span.get_text(separator=' ', strip=True)
                    if span_text:
                        article_content.append(span_text)

                links = element.find_all('a')
                for link in links:
                    link_text = link.get_text(separator=' ', strip=True)
                    if link_text:
                        article_content.append(link_text)

        # Find the main article container using the cp-article tag
        cp_articles = soup.find_all('cp-article')
        
        for cp_article in cp_articles:
            # Extract text from paragraphs with the specific data-t attribute within cp-article
            paragraphs = cp_article.find_all('p', {'data-t': 'n:bluelinks'})
            extract_text(paragraphs)
        
        # If no cp-article elements are found, fallback to extracting from the whole document
        if not article_content:
            # Potential tags and attributes to find article content
            potential_tags = ['div', 'p', 'span', 'article', 'section']
            potential_classes = ['article-body', 'article-content', 'content', 'main-content', 'post-content', 'entry-content']
            potential_attributes = {'data-t': 'n:bluelinks'}

            # Extract text from elements with specified tags and classes within the whole document
            for tag in potential_tags:
                for class_name in potential_classes:
                    elements = soup.find_all(tag, class_=class_name)
                    extract_text(elements)

            # Extract text from elements with specific attributes within the whole document
            for tag in potential_tags:
                elements = soup.find_all(tag, attrs=potential_attributes)
                extract_text(elements)

        # Clean up and return the concatenated article content
        return ' '.join(article_content).strip() if article_content else "Article content not found"
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        return None
    except AttributeError as e:
        print(f"Attribute Error: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    

def generate_filename(base_name):
    """
    Generate a filename that incorporates the current date and time.
    
    Args:
    base_name (str): The base name for the file, without the date-time part.
    
    Returns:
    str: A filename with the current date and time appended.
    """
    # Get the current date and time
    now = datetime.datetime.now()
    
    # Format the date and time to a string, e.g., '2022-04-26_15-30-25'
    datetime_string = now.strftime("%Y-%m-%d_%H-%M-%S")
    
    # Create the filename
    filename = f"{base_name}_Summaries_{datetime_string}.html"
    
    return filename


# Call the test function
def search_bing_news(query, role):

    endpoint = "https://api.bing.microsoft.com/v7.0/news/search"

    headers = {'Ocp-Apim-Subscription-Key': BING_SEARCH_API}
    # if role=='writer':
    #     analyst_names = ["Adam Jonas", "Dan Ives", "Cathie Wood"]  # List of prominent analysts
    #     #analyst_names=''
    #     query += " " + " OR ".join(analyst_names)
        
    
    params = {
        'q': query,  # Query can be changed as needed
        'mkt': 'en-US',
        'count': 10
    }
    summaries =[]
    
    
    response = requests.get(endpoint, headers=headers, params=params)

    try:
        response.raise_for_status()
        results = response.json()
        for article in results['value']:
            # Extract title, URL, and description
            title = article.get('name', 'No title available')
            url = article.get('url', 'No URL available')
            description = article.get('description', 'No description available')
            summary = 'failed to parse the webpage'

            # Example URL from your news search
            article_url = url
            content = get_full_article_content(article_url)

            print(f"Title: {title}")
            print(f"URL: {url}")
            print(f"Description: {description}")
            print("--------------------------------------------------")
            if content is not None:
                print(f"Content: {content}")
                if content != 'Article content not found':
                    summary = enhance_description_llama(content, role)
                else:
                    summary +='\n'+description
                
                summaries.append((title, summary, url))


    except requests.exceptions.HTTPError as e:
        print("HTTP Error:", e)
    except Exception as e:
        print("Error:", e)


def summarize_pdf_old(file_path):
    # Extract file name and extension
    file_name = os.path.basename(file_path)
    title = os.path.splitext(file_name)[0]
    
    try:
        # Load the PDF
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        # Split the document
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)
        
        # Set up the Llama3 model
        llm = Ollama(model="llama3")
        
        # Create the summarization chain
        chain = load_summarize_chain(llm, chain_type="map_reduce")
        
        # Generate the summary
        summary = chain.run(texts)
        
        # Return the tuple (title, summary, url)
        return (title, summary.strip(), file_path)
    
    except Exception as e:
        print(f"An error occurred while summarizing the PDF: {e}")
        return (title, "Error: Unable to summarize the PDF.", file_path)

def summarize_pdf(file_path):
    # Extract file name and extension
    file_name = os.path.basename(file_path)
    title = os.path.splitext(file_name)[0]
    
    try:
        # Load the PDF
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        # Split the document with smaller chunk size
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=20,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        texts = text_splitter.split_documents(documents)
        
        # Set up the Llama3 model
        llm = Ollama(model="llama3")
        
        # Create the summarization chain
        chain = load_summarize_chain(llm, chain_type="map_reduce")
        
        # Generate the summary using invoke instead of run
        summary = chain.invoke({"input_documents": texts})
        
        # Ensure summary is a string
        if isinstance(summary, dict) and 'output_text' in summary:
            summary = summary['output_text']
        elif not isinstance(summary, str):
            summary = str(summary)
        
        # Return the tuple (title, summary, url)
        return (title, summary.strip(), file_path)
    
    except Exception as e:
        print(f"An error occurred while summarizing the PDF: {e}")
        return (title, f"Error: Unable to summarize the PDF. {str(e)}", file_path)





if __name__ == "__main__":

    try:
        # Code block

        parser = argparse.ArgumentParser(description='YouTube and News Summary Generator')
        parser.add_argument('--search_query', default='Tesla or Nvidia stock news',type=str, help='The search query for YouTube and news')
        parser.add_argument('--role', type=str, default='writer',help='The role for summarization context')

        args = parser.parse_args()

        search_query = args.search_query
        role = args.role


        first_word = search_query.split()[0]  # Get the first word of the query for the filename
        print(role)
        filename_v = generate_filename(f'{first_word}+_v')
        # filename_t = generate_filename(f'{first_word}+_t')
        
        summaries = youtube_search(search_query, role)
        create_html_page(summaries, filename_v)
        
        # summaries_b = search_bing_news(search_query, role)
        # create_html_page(summaries_b, filename_t)
        
        #file_path = 'C:\Dropbox\패밀리룸\heegul(2024-)\papers\-Blind and Channel-agnostic Equalization Using Adversarial Networks-.pdf'
        #filename_p = generate_filename(f'pdf+_t')
        #summary_pdf = summarize_pdf(file_path)
        #create_html_page(summary_pdf, filename_p)




        # models = openai.Model.list()

        # for model in models['data']:
        #     print(f"Model ID: {model['id']} | Model Name: {model.get('name', 'N/A')}")


    except Exception as e:
        logging.error(f"An error occurred: {e}")
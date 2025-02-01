import os
import json
import re
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
import requests
from youtube_transcript_api import YouTubeTranscriptApi

# Directory paths
pdf_dir = r"C:\Dropbox\패밀리룸\heegul(2024-)\papers"
jsonl_file = 'output_data_pdf.jsonl'

# Function to extract text from PDFs
def extract_text_from_pdfs(pdf_dir):
    pdf_texts = []
    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.endswith('.pdf'):
            with open(os.path.join(pdf_dir, pdf_file), 'rb') as file:
                reader = PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
                pdf_texts.append(text)
    return pdf_texts

# Function to extract text from web pages
def extract_text_from_web(urls):
    web_texts = []
    for url in urls:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        web_texts.append(soup.get_text())
    return web_texts

# Function to extract text from YouTube videos
def extract_text_from_youtube(video_ids):
    youtube_texts = []
    for video_id in video_ids:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = ' '.join([item['text'] for item in transcript])
        youtube_texts.append(text)
    return youtube_texts

# Function to clean text
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # Remove extra whitespaces
    text = re.sub(r'\[.*?\]', '', text)  # Remove content in brackets
    return text.strip()

# Function to format data into JSONL
def format_to_jsonl(data, jsonl_file):
    with open(jsonl_file, 'w') as file:
        for item in data:
            prompt = item.get('prompt', '')
            completion = item.get('completion', '')
            jsonl_entry = {
                "prompt": f"{prompt}\nAnswer:",
                "completion": f" {completion}"
            }
            file.write(json.dumps(jsonl_entry) + '\n')

# Main function to orchestrate the data extraction and cleaning
def main():
    pdf_texts = extract_text_from_pdfs(pdf_dir)
    #web_urls = ['https://example.com/page1', 'https://example.com/page2']  # Replace with actual URLs
    #web_texts = extract_text_from_web(web_urls)
    #youtube_video_ids = ['abc123', 'def456']  # Replace with actual video IDs
    #youtube_texts = extract_text_from_youtube(youtube_video_ids)
    
    # Combine all texts
    #all_texts = pdf_texts + web_texts + youtube_texts
    #all_text = pdf_texts
    cleaned_texts = [clean_text(text) for text in pdf_texts]
    
    # Prepare data for JSONL
    data = [{'prompt': f"Extracted content:\n{text}\nSummary:", 'completion': ' [Your desired summary here]'} for text in cleaned_texts]
    format_to_jsonl(data, jsonl_file)

    print(f"Data extraction and cleaning complete. Output saved to {jsonl_file}")

if __name__ == "__main__":
    main()

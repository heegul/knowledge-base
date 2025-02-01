import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import webbrowser
import os

# Suppress symlinks warning on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Initialize the summarization pipeline with a specific model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Function to fetch web content
def fetch_web_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Function to create and open summarized HTML
def create_and_open_html(summary, title="Summarized Content"):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
    </head>
    <body>
        <h1>{title}</h1>
        <p>{summary}</p>
    </body>
    </html>
    """
    with open("summary.html", "w", encoding="utf-8") as file:
        file.write(html_content)
    webbrowser.open("summary.html")

# Main function
def main():
    # Get search query from user
    query = input("Enter your search query: ")
    search_url = f"https://www.google.com/search?q={query}"

    # Fetch search results page
    html_content = fetch_web_content(search_url)
    if not html_content:
        return

    # Parse HTML and extract text
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text()

    # Summarize the text
    summary = summarizer(text, max_length=130, min_length=30, do_sample=False)[0]['summary_text']

    # Create and open summarized HTML
    create_and_open_html(summary, title=f"Summary for: {query}")

if __name__ == "__main__":
    main()
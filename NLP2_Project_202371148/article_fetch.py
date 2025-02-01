import requests
from bs4 import BeautifulSoup
from summary import get_summary
import datetime

def fetch_article_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch article. Status code: {response.status_code}")
        return None

def check_login_required(content):
    login_keywords = ['sign in', 'log in', 'subscribe', 'paywall']
    soup = BeautifulSoup(content, 'html.parser')
    text_content = soup.get_text().lower()
    for keyword in login_keywords:
        if keyword in text_content:
            return True
    return False
def get_article_info(url,content_type='default'):
    try:
        content = fetch_article_content(url)
        if content:
            if check_login_required(content):
                print("Login is required to access this article.")
                return None, None, None, None
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.find('title').text
            paragraphs = soup.find_all('p')
            content = '\n'.join([para.text for para in paragraphs])
            summary = get_summary(content, content_type)
            date = datetime.datetime.now().date()
            return title, summary, url, date
        return None, None, None, None
    except Exception as e:
        print(f"An error occurred while fetching the article: {e}")
        return None, None, None, None

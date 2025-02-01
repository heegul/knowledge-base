import requests

from bs4 import BeautifulSoup


def get_full_article_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # This is an example; you'll need to tailor the tag/class based on the site's structure
        article_content = soup.find('article').text
        return article_content
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")






def search_bing_news():
    api_key = "727816d96fdd47e899a8cf764ad61020"  # Your Bing News API key
    endpoint = "https://api.bing.microsoft.com/v7.0/news/search"

    headers = {'Ocp-Apim-Subscription-Key': api_key}
    params = {
        'q': 'Tesla',  # Query can be changed as needed
        'mkt': 'en-US'
    }

    response = requests.get(endpoint, headers=headers, params=params)

    try:
        response.raise_for_status()
        results = response.json()
        for article in results['value']:
            # Extract title, URL, and description
            title = article.get('name', 'No title available')
            url = article.get('url', 'No URL available')
            description = article.get('description', 'No description available')

            # Example URL from your news search
            article_url = url
            content = get_full_article_content(article_url)
            #print(content)

            print(f"Title: {title}")
            print(f"URL: {url}")
            print(f"Description: {description}")
            print("--------------------------------------------------")
            if content is not None:
                print(f"Content: {content}")
    except requests.exceptions.HTTPError as e:
        print("HTTP Error:", e)
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    search_bing_news()

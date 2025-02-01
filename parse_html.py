import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

url = "https://www.msn.com/en-us/money/companies/can-elon-musk-make-tesla-stock-more-valuable-than-nvidia-with-ai-products/ar-BB1hVLo1"
url = "https://www.comsoc.org/publications/best-readings/machine-learning-communications#sd"
# Test with different User-Agents
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'
]

for ua in user_agents:
    headers = {'User-Agent': ua}
    response = requests.get(url, headers=headers)
    print(f"Status Code with User-Agent {ua}: {response.status_code}")
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.find('p', string=lambda text: 'Elon Musk' in text if text else False)
    if content:
        print(f"Content found with User-Agent {ua}: {content.text[:100]}...")
    else:
        print(f"No content found with User-Agent {ua}")

# Test with Selenium (JavaScript rendering)
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(url)

try:
    content = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Elon Musk')]"))
    )
    print(f"Content found with Selenium: {content.text[:100]}...")
except Exception as e:
    print(f"No content found with Selenium. Error: {e}")

# Print all paragraph texts to see what's actually on the page
paragraphs = driver.find_elements(By.TAG_NAME, "p")
print("All paragraph texts:")
for i, p in enumerate(paragraphs):
    print(f"Paragraph {i+1}: {p.text[:100]}...")

driver.quit()
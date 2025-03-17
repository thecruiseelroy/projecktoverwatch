import requests
from bs4 import BeautifulSoup

class URLScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def clean_text(self, text):
        return ' '.join(text.split())

    def extract_main_content(self, soup):
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda x: x and 'content' in x)
        if not main_content:
            return None
        
        for element in main_content(['script', 'style', 'nav', 'footer', 'iframe', 'form', 'header', 'aside', 'noscript']):
            element.decompose()
            
        return main_content

    def scrape_url_content(self, url: str) -> dict:
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            main_content = self.extract_main_content(soup)
            
            if not main_content:
                return {
                    'title': soup.title.string if soup.title else 'No Title',
                    'content': 'No main content found'
                }
            
            content = []
            title = soup.find('title')
            
            for element in main_content.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'blockquote']):
                if element.name in ['h1', 'h2', 'h3']:
                    content.append(self.clean_text(element.get_text()))
                elif element.name == 'p':
                    text = self.clean_text(element.get_text())
                    if len(text) > 50:
                        content.append(text)
                elif element.name in ['ul', 'ol']:
                    for li in element.find_all('li'):
                        content.append(self.clean_text(li.get_text()))
                elif element.name == 'blockquote':
                    content.append(self.clean_text(element.get_text()))
            
            return {
                'title': self.clean_text(title.get_text()) if title else 'No Title',
                'content': '\n'.join(content)
            }
            
        except Exception as e:
            return {
                'title': 'Error',
                'content': f"Error scraping {url}: {str(e)}"
            }

    def scrape_all_urls(self, urls: list) -> dict:
        results = {}
        for url in urls:
            results[url] = self.scrape_url_content(url)
        return results

if __name__ == "__main__":
    scraper = URLScraper()
    test_urls = [
        'https://www.example.com',
        'https://www.another-example.com'
    ]
    results = scraper.scrape_all_urls(test_urls) 
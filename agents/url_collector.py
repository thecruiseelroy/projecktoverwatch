import requests
import base64
import json
import datetime
from urllib.parse import urlparse

class URLCollector:
    def __init__(self):
        self.cred = self._get_credentials()
        self.social_media_domains = [
            'twitter.com', 'x.com',
            'facebook.com', 'instagram.com',
            'linkedin.com', 'pinterest.com', 
            'reddit.com', 'tiktok.com', 
            'youtube.com', 'whatsapp.com'
        ]

    def _get_credentials(self):
        with open('config.json') as config_file:
            config = json.load(config_file)
        api_login = config['dataforseo']['api_login']
        api_password = config['dataforseo']['api_password']
        return base64.b64encode(f"{api_login}:{api_password}".encode()).decode()

    def is_social_media(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return any(sm_domain in domain for sm_domain in self.social_media_domains)

    def get_serp_results(self, keyword: str, max_urls: int = 10) -> list:
        url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
        payload = json.dumps([{
            "keyword": keyword,
            "location_code": 2840,
            "language_code": "en"
        }])
        
        headers = {
            'Authorization': f'Basic {self.cred}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=payload)
        raw_results = response.json()['tasks'][0]['result'][0]['items']
        
        filtered_urls = []
        for item in raw_results:
            if 'url' in item and item['url']:
                url_lower = item['url'].lower()
                if 'google.com/search' in url_lower:
                    continue
                if not self.is_social_media(item['url']):
                    filtered_urls.append({
                        'url': item['url'],
                        'collected_at': datetime.datetime.now().isoformat(),
                        'source': urlparse(url_lower).netloc
                    })
        
        return sorted(filtered_urls[:max_urls], 
                     key=lambda x: x['collected_at'],
                     reverse=True)

if __name__ == "__main__":
    collector = URLCollector()
    urls = collector.get_serp_results("claudes anthropic latest funding round")
    print(f"Found {len(urls)} URLs:")
    for url in urls:
        print(f"{url} collected at {datetime.datetime.now().isoformat()}") 
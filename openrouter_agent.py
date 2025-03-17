import requests
import json

class OpenRouterAgent:
    def __init__(self, api_key: str, site_url: str, site_name: str, model: str):
        self.api_key = api_key
        self.site_url = site_url
        self.site_name = site_name
        self.model = model

    def summarize(self, content: str) -> str:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.site_url,
                "X-Title": self.site_name,
            },
            json={
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": f"Summarize this content in 3-5 bullet points:\n\n{content[:5000]}"
                }]
            }
        )
        return response.json()['choices'][0]['message']['content'] 
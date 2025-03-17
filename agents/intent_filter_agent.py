import requests
import json

class IntentFilterAgent:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def _call_api(self, messages: list, stream: bool = True) -> str:
        response = requests.post(
            url=self.url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": messages,
                "stream": stream
            },
            stream=stream
        )
        
        if stream:
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        json_response = json.loads(line.decode('utf-8').split('data: ')[1])
                        if 'choices' in json_response:
                            content = json_response['choices'][0].get('delta', {}).get('content', '')
                            if content:
                                print(content, end='', flush=True)
                                full_response += content
                    except:
                        continue
            print()
            return full_response
        else:
            data = response.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content']
            elif 'error' in data:
                return f"API Error: {data['error']['message']}"
            return "No valid response from API"

    def determine_domain(self, query: str) -> str:
        prompt = f"""Analyze this query and determine the most appropriate domain expertise required:
        
Query: "{query}"

Respond with ONLY the domain expertise persona required in this format:
[Domain]: [Specific Expertise]

Examples: political report, mathematician, doctor, etc."""

        return self._call_api([{
            "role": "user",
            "content": prompt
        }], stream=True) 
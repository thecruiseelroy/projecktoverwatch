import requests
import json
import datetime

class OpenRouterAgent:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def _call_api(self, messages: list, stream: bool = False) -> str:
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
            for chunk in response.iter_lines():
                if chunk:
                    try:
                        chunk_str = chunk.decode('utf-8')
                        if chunk_str.startswith("data: "):
                            if chunk_str == "data: [DONE]":
                                continue
                            try:
                                data = json.loads(chunk_str[6:])
                                if 'choices' in data:
                                    delta = data['choices'][0]['delta']
                                    if 'content' in delta:
                                        full_response += delta['content']
                            except json.JSONDecodeError:
                                continue
                    except Exception as e:
                        print(f"\nError processing stream: {str(e)}")
            return full_response
        else:
            data = response.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content']
            elif 'error' in data:
                return f"API Error: {data['error']['message']}"
            return "No valid response from API"

    def summarize(self, content: str) -> str:
        return self._call_api([{
            "role": "user",
            "content": f"Summarize this content in 3-5 bullet points:\n\n{content[:5000]}"
        }], stream=True)

    def generate_report(self, structured_data: list, query: str) -> str:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        prompt = f"""Create a report based ONLY on the following verified data to answer: "{query}"

Current Time: {current_time}

Verified Data:
{json.dumps(structured_data, indent=2)}

Rules:
1. Use ONLY the provided data
2. Do not add any external information
3. If data conflicts, present all perspectives
4. Clearly indicate source IDs for each fact
5. Maintain neutral tone
6. If insufficient data, state what's missing
7. Consider the current time ({current_time}) as the present moment

Format as:
# Report: [Query]

## Findings
- [Key findings from data]

## Sources
- [List of sources with IDs]"""

        return self._call_api([{
            "role": "user",
            "content": prompt
        }], stream=True)

    def _identify_domain(self, query: str) -> str:
        # Simple domain identification based on keywords
        query_lower = query.lower()
        if any(word in query_lower for word in ['health', 'medical', 'disease']):
            return 'health and medicine'
        elif any(word in query_lower for word in ['tech', 'computer', 'software']):
            return 'technology'
        elif any(word in query_lower for word in ['law', 'legal', 'regulation']):
            return 'law and policy'
        elif any(word in query_lower for word in ['finance', 'economy', 'stock']):
            return 'finance and economics'
        elif any(word in query_lower for word in ['science', 'research', 'study']):
            return 'scientific research'
        return 'general knowledge' 
import requests
import json
from typing import List, Dict

class BaseAgent:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def _call_api(self, messages: list, stream: bool = True, max_tokens: int = 4000) -> str:
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
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
                print()  # Add newline after streaming
                return full_response
            else:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content']
                else:
                    print("\nError: Invalid API response format")
                    return "Error: Invalid API response"
        except Exception as e:
            print(f"\nAPI call error: {str(e)}")
            return f"Error in API call: {str(e)}"

    def generate_report(self, structured_data: List[Dict], query: str) -> str:
        if not structured_data:
            return "Error: No data provided"
        
        try:
            # Validate structured data format
            for item in structured_data:
                required_keys = ['source_id', 'url', 'collected_at', 'content']
                if not all(key in item for key in required_keys):
                    return "Error: Invalid data structure"
            
            # Get and validate plan
            plan = self.planner.plan_report(query)
            if not plan or len(plan.strip()) == 0:
                return "Error: Failed to generate report plan"
            
            # Implement report generation logic
            # This is a placeholder and should be replaced with actual implementation
            return "Report generation logic not implemented"
        except Exception as e:
            return f"Error: {e}" 
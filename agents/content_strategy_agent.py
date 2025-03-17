from datetime import datetime
from .base_agent import BaseAgent

class ContentStrategyAgent(BaseAgent):
    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)

    def create_content_strategy(self, query: str) -> str:
        messages = [{
            "role": "you are a seo content researcher, creating a content brief",
            "content": """You are a query-focused fact verifier.
CRITICAL RULES:
- Questions MUST be specific to the exact query
- NO generic questions
- NO asking about things not in query
- Questions should verify ONLY what was asked
- NO extra context questions
- STAY FOCUSED on query intent"""
        }, {
            "role": "user",
            "content": f"""Generate atleast 10 questions that ONLY verify facts about: "{query}"

For example, if query is "last bivol boxing match results":
1. What was the final result of Bivol's most recent fight?
2. Who was Bivol's opponent in his last match?
3. When and where did this fight take place?"""
        }]

        return self._call_api(messages, stream=True) 
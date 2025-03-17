import json
from .base_agent import BaseAgent
from datetime import datetime

class ReportPlannerAgent(BaseAgent):
    def plan_report(self, query: str) -> str:
        messages = [{
            "role": "system",
            "content": """You are a simple outline creator.
CRITICAL RULES:
- Create only 3-4 basic headers
- NO sub-headers or nested structure
- NO specific details or numbers
- NO dates or statistics
- PURE high-level categories only
- Keep it extremely simple"""
        }, {
            "role": "user",
            "content": f"""Create a basic outline for: "{query}"
Only output 3-4 main headers that would organize basic facts about the topic."""
        }]

        return self._call_api(messages, stream=False) 
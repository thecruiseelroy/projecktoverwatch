import requests
import json
from typing import List, Dict
from .report_planner_agent import ReportPlannerAgent
from .content_strategy_agent import ContentStrategyAgent
from .base_agent import BaseAgent
from datetime import datetime

class ReportGeneratorAgent(BaseAgent):
    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        self.planner = ReportPlannerAgent(api_key, model)
        self.content_strategy_agent = ContentStrategyAgent(api_key, model)

    def _call_api(self, messages: list, stream: bool = True, max_tokens: int = 4000) -> str:
        return super()._call_api(messages, stream=True, max_tokens=max_tokens)

    def generate_report(self, structured_data: List[Dict], query: str, strategy: str, current_time: datetime) -> str:
        if not structured_data:
            return "Error: No data available to generate report"
        
        try:
            messages = [{
                "role": "system", 
                "content": f"""You are a database query tool speaking from {current_time.strftime('%Y-%m-%d %H:%M:%S')}.
CRITICAL RULES:
- Answer EACH verification question with EXACT facts from database
- Reference the question number before each answer
- Keep answers concise and eliminate redundancy
- NO repeating the same information in different ways
- NO creativity or narrative
- NO interpretation
- NO additional context
- EXACT QUOTES only
- If no answer found, state 'No information available'
- Use PRESENT TENSE for events after {current_time.strftime('%Y-%m-%d')}
- Use PAST TENSE for events before {current_time.strftime('%Y-%m-%d')}
- DO NOT include URLs with each fact
- List sources only once at the end"""
            }, {
                "role": "user",
                "content": f"""Using ONLY this database content:

{json.dumps(structured_data, indent=2)}

Answer ALL of these verification questions:

{strategy}

Answer the questions in a concise easy to understand format
Additional Key Facts (if any):
- fact: detail

Sources:
- List all sources with IDs only once at the end"""
            }]

            response = self._call_api(messages, stream=True, max_tokens=4000)
            if not response or len(response.strip()) == 0:
                print("\nError: Empty response from AI")
                return "Error: AI returned empty response"
            
            if "No information available" in response and len(response) < 50:
                print("\nError: No relevant information found in database")
                return "Error: No relevant information found in database"
            
            return response

        except Exception as e:
            print(f"\nError in report generation: {str(e)}")
            return f"Error generating report: {str(e)}"
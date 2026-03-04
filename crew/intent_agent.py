"""
Intent Agent - анализ свободного текста пользователя через OpenAI
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import re

load_dotenv()


class IntentAgent:
    """Агент для извлечения намерений из текста"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("PROXYAPI_KEY"),
            base_url=os.getenv("PROXYAPI")
        )
    
    def analyze(self, text: str) -> dict:
        """Анализирует текст и возвращает структурированные данные."""
        
        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": """Ты эксперт по туризму. Верни JSON с ключами:
- budget: бюджет в USD (число)
- season: сезон (winter/spring/summer/autumn)
- climate: климат (warm/temperate/cold)
- visa_required: нужна ли виза (true/false)
- travel_type: тип отдыха (beach/mountains/city/adventure)
- with_children: с детьми (true/false)
- safety_priority: приоритет безопасности (low/medium/high)

Верни ТОЛЬКО JSON."""},
                {"role": "user", "content": text}
            ],
            temperature=0
        )
        
        result = response.choices[0].message.content
        
        try:
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
        
        return {}


if __name__ == '__main__':
    agent = IntentAgent()
    print(agent.analyze("Хочу тепло, без визы, бюджет 1500"))
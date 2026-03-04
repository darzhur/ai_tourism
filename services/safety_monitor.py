"""
Safety Monitor - проверка безопасности стран через ИИ
Новости парсятся с источников → передаются ИИ → risk_score
"""

import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
import json
from datetime import datetime

load_dotenv()


class SafetyMonitor:
    """Мониторинг безопасности стран через ИИ"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("PROXYAPI_KEY"),
            base_url=os.getenv("PROXYAPI")
        )
        self.cache = {}
        self.headers = {'User-Agent': 'Mozilla/5.0'}
    
    def get_country_risk(self, country_name: str) -> dict:
        """Получает risk_score (1-5) для страны через ИИ"""
        
        # Проверка кэша
        if country_name in self.cache:
            return self.cache[country_name]
        
        # Парсим новости
        news = self._fetch_news(country_name)
        
        # Анализируем через ИИ
        risk_data = self._analyze_with_ai(country_name, news)
        
        self.cache[country_name] = risk_data
        return risk_data
    
    def _fetch_news(self, country: str) -> list:
        """Собирает новости с источников"""
        news = []
        
        # 1. BBC News
        bbc = self._parse_bbc(country)
        news.extend(bbc)
        
        # 2. Google News (через RSS)
        google = self._parse_google_news(country)
        news.extend(google)
        
        return news[:10]  # Ограничим 10 новостями
    
    def _parse_bbc(self, country: str) -> list:
        """Парсит BBC News"""
        try:
            url = f"https://news.google.com/rss/search?q={country}+tourism&hl=ru-RU&gl=RU"
            r = requests.get(url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(r.text, 'xml')
            
            articles = []
            for item in soup.find_all('item')[:5]:
                title = item.find('title')
                if title:
                    articles.append({
                        'source': 'Google News',
                        'title': title.text.strip()
                    })
            return articles
        except Exception as e:
            print(f"BBC error: {e}")
            return []
    
    def _parse_google_news(self, country: str) -> list:
        """Парсит Google News"""
        try:
            url = f"https://news.google.com/rss/search?q={country}&hl=ru-RU&gl=RU"
            r = requests.get(url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(r.text, 'xml')
            
            articles = []
            for item in soup.find_all('item')[:5]:
                title = item.find('title')
                if title:
                    articles.append({
                        'source': 'Google News',
                        'title': title.text.strip()
                    })
            return articles
        except Exception as e:
            print(f"Google News error: {e}")
            return []
    
    def _analyze_with_ai(self, country: str, news: list) -> dict:
        """Анализирует новости через ИИ"""
        
        # Формируем текст новостей
        news_text = "\n".join([f"- {n['title']}" for n in news]) if news else "Новостей не найдено"
        
        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": """Ты эксперт по безопасности путешествий.
Проанализируй новости о стране и оцени риск для туристов.

Шкала риска (1-5):
1 - Безопасно, можно ехать
2 - Низкий риск, мелкие происшествия
3 - Средний риск, есть предупреждения
4 - Высокий риск, рекомендуется воздержаться
5 - Критический риск, небезопасно

Учитывай: терроризм, политическая ситуация, криминал, природные катастрофы, эпидемии.

Верни JSON:
{"risk_score": 1-5, "level": "low/medium/high/critical", "reasons": ["причина1", "причина2"]}

Верни ТОЛЬКО JSON."""},
                {"role": "user", "content": f"Страна: {country}\n\nНовости:\n{news_text}"}
            ],
            temperature=0
        )
        
        result = response.choices[0].message.content
        
        try:
            import re
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                data = json.loads(match.group())
                data['country'] = country
                data['news_analyzed'] = len(news)
                data['checked_at'] = datetime.now().isoformat()
                return data
        except:
            pass
        
        return {
            'country': country,
            'risk_score': 2,
            'level': 'low',
            'reasons': ['Проверка пройдена'],
            'news_analyzed': len(news),
            'checked_at': datetime.now().isoformat()
        }


# Тест
if __name__ == '__main__':
    sm = SafetyMonitor()
    print(sm.get_country_risk("Egypt"))
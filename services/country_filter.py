"""
Поиск стран по критериям
Фильтрация + сортировка по релевантности → топ-10
"""

import json
import os
from typing import Dict, List, Any, Optional


# База стран
COUNTRIES_DB = [
    {
        "country": "Spain",
        "avg_price": 1400,
        "visa_required": False,
        "best_season": ["summer", "spring", "autumn"],
        "climate": "warm",
        "travel_type": ["beach", "city"],
        "safety_level": "high",
        "with_children": True,
        "flight_duration": 4,
    },
    {
        "country": "Turkey",
        "avg_price": 900,
        "visa_required": False,
        "best_season": ["summer", "spring"],
        "climate": "warm",
        "travel_type": ["beach"],
        "safety_level": "medium",
        "with_children": True,
        "flight_duration": 3,
    },
    {
        "country": "Egypt",
        "avg_price": 800,
        "visa_required": True,
        "best_season": ["winter", "autumn", "spring"],
        "climate": "warm",
        "travel_type": ["beach"],
        "safety_level": "medium",
        "with_children": True,
        "flight_duration": 5,
    },
    {
        "country": "Greece",
        "avg_price": 1200,
        "visa_required": False,
        "best_season": ["summer", "spring"],
        "climate": "warm",
        "travel_type": ["beach", "city"],
        "safety_level": "high",
        "with_children": True,
        "flight_duration": 3,
    },
    {
        "country": "Thailand",
        "avg_price": 1100,
        "visa_required": False,
        "best_season": ["winter", "autumn"],
        "climate": "warm",
        "travel_type": ["beach", "adventure"],
        "safety_level": "medium",
        "with_children": True,
        "flight_duration": 10,
    },
    {
        "country": "Italy",
        "avg_price": 1500,
        "visa_required": False,
        "best_season": ["summer", "spring", "autumn"],
        "climate": "warm",
        "travel_type": ["city", "beach"],
        "safety_level": "high",
        "with_children": True,
        "flight_duration": 4,
    },
    {
        "country": "France",
        "avg_price": 1600,
        "visa_required": False,
        "best_season": ["summer", "spring", "autumn"],
        "climate": "temperate",
        "travel_type": ["city"],
        "safety_level": "high",
        "with_children": True,
        "flight_duration": 4,
    },
    {
        "country": "Portugal",
        "avg_price": 1300,
        "visa_required": False,
        "best_season": ["summer", "spring", "autumn"],
        "climate": "warm",
        "travel_type": ["beach", "city"],
        "safety_level": "high",
        "with_children": True,
        "flight_duration": 5,
    },
    {
        "country": "UAE",
        "avg_price": 1800,
        "visa_required": True,
        "best_season": ["winter", "autumn", "spring"],
        "climate": "warm",
        "travel_type": ["beach", "city"],
        "safety_level": "high",
        "with_children": True,
        "flight_duration": 6,
    },
    {
        "country": "Mexico",
        "avg_price": 1400,
        "visa_required": False,
        "best_season": ["winter", "autumn"],
        "climate": "warm",
        "travel_type": ["beach", "adventure"],
        "safety_level": "medium",
        "with_children": True,
        "flight_duration": 12,
    },
    {
        "country": "Japan",
        "avg_price": 2000,
        "visa_required": True,
        "best_season": ["spring", "autumn"],
        "climate": "temperate",
        "travel_type": ["city", "adventure"],
        "safety_level": "high",
        "with_children": True,
        "flight_duration": 11,
    },
    {
        "country": "Georgia",
        "avg_price": 700,
        "visa_required": False,
        "best_season": ["summer", "spring", "autumn"],
        "climate": "temperate",
        "travel_type": ["mountains", "city", "adventure"],
        "safety_level": "high",
        "with_children": True,
        "flight_duration": 3,
    },
]


class CountryFilter:
    """Фильтрация и сортировка стран"""
    
    def __init__(self, countries: List[Dict] = None):
        self.countries = countries or COUNTRIES_DB
    
    def search(self, criteria: Dict[str, Any], limit: int = 10) -> List[Dict]:
        """
        Поиск стран по критериям.
        
        Алгоритм:
        1. Фильтрация по обязательным критериям
        2. Сортировка по релевантности
        3. Ограничение top-N
        """
        # Шаг 1: Фильтрация
        filtered = self._filter_countries(criteria)
        
        # Шаг 2: Сортировка по релевантности
        scored = self._score_countries(filtered, criteria)
        
        # Шаг 3: Ограничение
        return scored[:limit]
    
    def _filter_countries(self, criteria: Dict[str, Any]) -> List[Dict]:
        """Фильтрация по exact match"""
        result = []
        
        for country in self.countries:
            match = True
            
            # visa_required (boolean)
            if 'visa_required' in criteria:
                if country['visa_required'] != criteria['visa_required']:
                    match = False
            
            # climate (exact match)
            if 'climate' in criteria and criteria['climate']:
                if country['climate'] != criteria['climate']:
                    match = False
            
            # travel_type (один из списка)
            if 'travel_type' in criteria and criteria['travel_type']:
                if criteria['travel_type'] not in country['travel_type']:
                    match = False
            
            # safety_priority
            if 'safety_priority' in criteria and criteria['safety_priority']:
                required = criteria['safety_priority']
                # high требует high, medium требует medium или high
                if required == 'high' and country['safety_level'] != 'high':
                    match = False
            
            # season
            if 'season' in criteria and criteria['season']:
                season_map = {
                    'winter': 'winter', 'зима': 'winter',
                    'spring': 'spring', 'весна': 'spring',
                    'summer': 'summer', 'лето': 'summer',
                    'autumn': 'autumn', 'осень': 'autumn',
                }
                season = season_map.get(criteria['season'], criteria['season'])
                if season not in country['best_season']:
                    match = False
            
            # budget (диапазон)
            if 'budget' in criteria and criteria['budget']:
                # Показываем страны в пределах budget + 30%
                if country['avg_price'] > criteria['budget'] * 1.3:
                    match = False
            
            # with_children
            if 'with_children' in criteria and criteria['with_children']:
                if not country.get('with_children', False):
                    match = False
            
            if match:
                result.append(country)
        
        return result
    
    def _score_countries(self, countries: List[Dict], criteria: Dict) -> List[Dict]:
        """Сортировка по релевантности"""
        scored = []
        
        for country in countries:
            score = 0
            
            # Точное совпадение travel_type = +10
            if 'travel_type' in criteria and criteria['travel_type']:
                if criteria['travel_type'] in country['travel_type']:
                    score += 10
            
            # Точное совпадение climate = +5
            if 'climate' in criteria and criteria['climate']:
                if criteria['climate'] == country['climate']:
                    score += 5
            
            # Близость к бюджету = +3
            if 'budget' in criteria and criteria['budget']:
                diff = abs(country['avg_price'] - criteria['budget'])
                if diff < criteria['budget'] * 0.1:
                    score += 3
                elif diff < criteria['budget'] * 0.2:
                    score += 1
            
            # Безопасность high = +2
            if country['safety_level'] == 'high':
                score += 2
            
            # Короткий перелёт = +1
            if country['flight_duration'] <= 5:
                score += 1
            
            scored.append({**country, 'relevance_score': score})
        
        # Сортировка по убыванию score
        scored.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return scored


# Тест
if __name__ == '__main__':
    cf = CountryFilter()
    
    # Тест 1: Только warm + beach
    result = cf.search({'climate': 'warm', 'travel_type': 'beach'})
    print("Тест 1: warm + beach")
    for c in result:
        print(f"  {c['country']} - {c['relevance_score']} баллов")
    
    print()
    
    # Тест 2: Без визы + бюджет 1000
    result = cf.search({'visa_required': False, 'budget': 1000})
    print("Тест 2: без визы + бюджет 1000")
    for c in result:
        print(f"  {c['country']} - {c['relevance_score']} баллов")
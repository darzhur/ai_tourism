"""
Research-парсер: парсит сайты → LLM → унифицированная схема критериев → форма
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any
import json
import os
from typing import Dict, List, Any, Optional
from services.safety_monitor import SafetyMonitor
from fastapi.responses import HTMLResponse


# Создать папку templates если нет
os.makedirs('templates', exist_ok=True)

# CRITERIA_SCHEMA - что анализируем (результат LLM)
CRITERIA_SCHEMA: Dict[str, str] = {}


# TYPE_MAPPING - как отображать разные типы критериев
TYPE_MAPPING = {
    "budget": "number",
    "flight_duration": "number",
    "visa_required": "boolean",
    "with_children": "boolean",
    "season": "select",
    "climate": "select",
    "travel_type": "select",
    "safety_level": "select",
    "safety_priority": "select",
    "food_preference": "select",
}


class TourParser:
    """Парсинг туристических сайтов"""
    
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0'}
    
    def parse_tour_operator(self, url: str) -> Dict:
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            return self._extract_filters(soup)
        except Exception as e:
            print(f"Ошибка: {e}")
            return {}
    
    def _extract_filters(self, soup):
        f = {'selects': [], 'checkboxes': [], 'ranges': []}
        for s in soup.find_all('select'):
            opts = [o.text.strip() for o in s.find_all('option') if o.text.strip()]
            if opts:
                f['selects'].append({'name': s.get('name', ''), 'options': opts[:20]})
        for c in soup.find_all('input', {'type': 'checkbox'}):
            if c.get('name'):
                f['checkboxes'].append(c.get('name'))
        for r in soup.find_all('input', {'type': 'range'}):
            if r.get('name'):
                f['ranges'].append(r.get('name'))
        return f


def get_demo_filters():
    return [
        {'selects': [
            {'name': 'country', 'options': ['Турция', 'Египет', 'Испания', 'Греция', 'Таиланд']},
            {'name': 'budget', 'options': ['до 50000', '50000-100000', '100000-200000']},
            {'name': 'season', 'options': ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']},
            {'name': 'climate', 'options': ['теплый', 'умеренный', 'холодный']},
            {'name': 'travel_type', 'options': ['пляжный', 'горный', 'экскурсионный']},
            {'name': 'safety_priority', 'options': ['низкий', 'средний', 'высокий']},
        ]},
        {'checkboxes': ['first_line', 'all_inclusive', 'with_children', 'wifi', 'pool']},
    ]


def parse_sources(urls: List[str] = None) -> Dict:
    parser = TourParser()
    result = {'tour_operators': [], 'articles': []}
    if not urls:
        result['tour_operators'] = get_demo_filters()
    return result


# Замени функцию extract_schema_via_llm:

def extract_schema_via_llm(parsed_data: Dict) -> Dict[str, str]:
    """LLM унифицирует критерии из сырых фильтров"""
    
    all_fields = set()
    for source in parsed_data.get('tour_operators', []):
        for sel in source.get('selects', []):
            all_fields.add(sel['name'])
        for cb in source.get('checkboxes', []):
            all_fields.add(cb)
    
    if not all_fields:
        return CRITERIA_SCHEMA
    
    fields_text = ", ".join(all_fields)
    
    try:
        from openai import OpenAI
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("PROXYAPI")
        )
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Унифицируй названия полей.

Обязательные поля: budget, season, climate, visa_required, travel_type, with_children, safety_level.

Верни JSON где ключи - унифицированные названия."""},
                {"role": "user", "content": f"Поля: {fields_text}"}
            ],
            temperature=0
        )
        
        result = response.choices[0].message.content
        import json, re
        match = re.search(r'\{.*\}', result, re.DOTALL)
        if match:
            criteria = json.loads(match.group())
    
    except Exception as e:
        print(f"LLM error: {e}")
        criteria = {}
    
    # ГАРАНТИРУЕМ ОБЯЗАТЕЛЬНЫЕ ПОЛЯ
    required_fields = {
        'budget': 'budget',
        'season': 'season', 
        'climate': 'climate',
        'visa_required': 'visa_required',
        'travel_type': 'travel_type',
        'with_children': 'with_children',
        'safety_level': 'safety_level',
    }
    
    for key, default in required_fields.items():
        if criteria.get(key) is None:
            criteria[key] = default
    
    return criteria

    """
    LLM унифицирует критерии из сырых фильтров.
    Возвращает CRITERIA_SCHEMA.
    """
    # Собираем все уникальные поля из парсинга
    all_fields = set()
    
    for source in parsed_data.get('tour_operators', []):
        for sel in source.get('selects', []):
            all_fields.add(sel['name'])
        for cb in source.get('checkboxes', []):
            all_fields.add(cb)
    
    if not all_fields:
        return CRITERIA_SCHEMA
    
    fields_text = ", ".join(all_fields)
    
    # Вызов LLM
    try:
        from openai import OpenAI
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        client = OpenAI(
            api_key=os.getenv("PROXYAPI_KEY"),
            base_url=os.getenv("PROXYAPI")
        )
        
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": """Ты эксперт по туристическим критериям.
Унифицируй названия полей фильтров.

Верни JSON где ключи - унифицированные названия:
- budget
- season
- climate
- visa_required
- flight_duration
- travel_type
- with_children
- safety_level
- food_preference

Верни ТОЛЬКО JSON."""},
                {"role": "user", "content": f"Поля с сайтов: {fields_text}"}
            ],
            temperature=0
        )
        
        result = response.choices[0].message.content
        import json, re
        match = re.search(r'\{.*\}', result, re.DOTALL)
        if match:
            return json.loads(match.group())
    
    except Exception as e:
        print(f"LLM error: {e}")
    
    # Заглушка если LLM не работает
    field_mapping = {
        'budget': 'budget', 'price': 'budget', 'cost': 'budget',
        'season': 'season', 'month': 'season',
        'climate': 'climate', 'weather': 'climate',
        'visa': 'visa_required',
        'travel_type': 'travel_type', 'type': 'travel_type',
        'children': 'with_children', 'family': 'with_children',
        'safety': 'safety_level', 'safe': 'safety_level',
    }
    
    criteria = {}
    for field in all_fields:
        normalized = field.lower().replace('-', '_').replace(' ', '_')
        criteria[field] = field_mapping.get(normalized, normalized)

    # Гарантируем обязательные поля
    for field in ['budget', 'season', 'climate', 'visa_required', 'travel_type', 'with_children', 'safety_level']:
        if criteria.get(field) is None:
            criteria[field] = field

    return criteria

    return criteria


def build_form_schema(criteria: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Строит FORM_SCHEMA на основе CRITERIA_SCHEMA.
    Динамически определяет тип поля.
    """
    form_schema = []
    
    for field_name in criteria.keys():
        field_type = TYPE_MAPPING.get(field_name, 'text')
        form_schema.append({
            "name": field_name,
            "type": field_type
        })
    
    return form_schema


def save_schema(schema: Dict, filepath: str = 'data/criteria_schema.json'):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)


def run_research():
    global CRITERIA_SCHEMA
    
    print("ЭТАП 1: Парсинг")
    parsed = parse_sources()
    print(f"Источников: {len(parsed['tour_operators'])}")
    
    print("\nЭТАП 2: LLM → CRITERIA_SCHEMA")
    CRITERIA_SCHEMA = extract_schema_via_llm(parsed)
    print(f"Критерии: {list(CRITERIA_SCHEMA.keys())}")
    
    print("\nЭТАП 3: CRITERIA_SCHEMA → FORM_SCHEMA")
    form_schema = build_form_schema(CRITERIA_SCHEMA)
    print(json.dumps(form_schema, ensure_ascii=False, indent=2))
    
    print("\nЭТАП 4: Сохранение")
    save_schema(CRITERIA_SCHEMA)
    
    return CRITERIA_SCHEMA, form_schema


# API
from fastapi import FastAPI, Body
from pydantic import BaseModel

app = FastAPI()


class IntentRequest(BaseModel):
    text: str


@app.get("/form-schema")
def get_form_schema():
    """Возвращает FORM_SCHEMA (построенную из CRITERIA_SCHEMA)"""
    if not CRITERIA_SCHEMA:
        run_research()
    return build_form_schema(CRITERIA_SCHEMA)


@app.get("/criteria-schema")
def get_criteria_schema():
    """Возвращает CRITERIA_SCHEMA"""
    if not CRITERIA_SCHEMA:
        run_research()
    return CRITERIA_SCHEMA


@app.post("/analyze-intent")
def analyze_intent(request: IntentRequest):
    """Анализирует свободный текст через Intent Agent"""
    try:
        from crew.intent_agent import IntentAgent
        agent = IntentAgent()
        intents = agent.analyze(request.text)
        return map_intents_to_form(intents)
    except ImportError:
        return {"error": "Intent Agent not implemented"}


def map_intents_to_form(intents: Dict[str, float]) -> Dict[str, Any]:
    """Преобразует результаты Intent Agent в данные формы"""
    form_data = {}
    
    if 'budget' in intents:
        form_data['budget'] = 1500
    if 'warm' in intents:
        form_data['climate'] = 'warm'
    elif 'cold' in intents:
        form_data['climate'] = 'cold'
    if 'visa_required' in intents:
        form_data['visa_required'] = False
    if 'beach' in intents:
        form_data['travel_type'] = 'beach'
    elif 'mountains' in intents:
        form_data['travel_type'] = 'mountains'
    elif 'culture' in intents:
        form_data['travel_type'] = 'city'
    if 'with_children' in intents:
        form_data['with_children'] = True
    if 'safety' in intents:
        form_data['safety_priority'] = 'high'
    
    return form_data


from services.country_filter import CountryFilter


class SearchRequest(BaseModel):
    budget: Optional[int] = None
    season: Optional[str] = None
    climate: Optional[str] = None
    visa_required: Optional[bool] = None
    travel_type: Optional[str] = None
    with_children: Optional[bool] = None
    safety_priority: Optional[str] = None


@app.post("/search-countries")
def search_countries(request: SearchRequest):
    """
    Поиск стран по критериям.
    POST /search-countries
    {"climate": "warm", "travel_type": "beach", "budget": 1000}
    """
    criteria = request.dict(exclude_none=True)
    
    cf = CountryFilter()
    results = cf.search(criteria, limit=10)
    
    return {
        "count": len(results),
        "results": results
    }

@app.get("/safety/{country}")
def get_safety(country: str):
    """Проверка безопасности страны: GET /safety/Spain"""
    sm = SafetyMonitor()
    return sm.get_country_risk(country)

# Добавить эндпоинт
@app.get("/", response_class=HTMLResponse)
def root():
    """Главная страница с формой"""
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        return f.read()
    
class FinalSearchRequest(BaseModel):
    budget: Optional[int] = None
    season: Optional[str] = None
    climate: Optional[str] = None
    visa_required: Optional[bool] = None
    travel_type: Optional[str] = None
    with_children: Optional[bool] = None
    safety_priority: Optional[str] = None
    free_text: Optional[str] = None


@app.post("/search")
def final_search(request: FinalSearchRequest):
    criteria = request.dict(exclude_none=True)
    
    # 1. Если есть свободный текст - обрабатываем через Intent Agent
    if request.free_text:
        try:
            from crew.intent_agent import IntentAgent
            agent = IntentAgent()
            intent_data = agent.analyze(request.free_text)
            for key, value in intent_data.items():
                if key not in criteria or criteria[key] is None:
                    criteria[key] = value
        except ImportError:
            pass
    
    # 2. Фильтрация стран
    cf = CountryFilter()
    countries = cf.search(criteria, limit=10)
    
    # 3. Добавляем risk_score через ИИ
    sm = SafetyMonitor()
    results = []
    
    for country in countries:
        risk = sm.get_country_risk(country['country'])
        results.append({
            **country,
            'risk_score': risk['risk_score'],
            'risk_level': risk['level'],
            'risk_reasons': risk.get('reasons', [])
        })
    
    # 4. Возвращаем
    return {
        "criteria_used": criteria,
        "count": len(results),
        "results": results
    }

if __name__ == '__main__':
    run_research()
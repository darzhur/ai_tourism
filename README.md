# AI Tourism
Система подбора туристических направлений с использованием ИИ.

## Описание
1. Парсинг сайтов туроператоров → LLM → схема критериев
2. Пользователь заполняет форму или пишет текст
3. LLM извлекает критерии из текста
4. Фильтрация стран по критериям (топ-10)
5. LLM + новости → risk_score для каждой страны

**Технологии:** FastAPI, OpenAI (через PROXYAPI), BeautifulSoup

## Архитектура

- .env # Переменные окружения
- .env.example # Пример переменных окружения
- crew/ 
- - intent_agent.py # Анализ намерений пользователя (LLM) 
- services/ 
- - research_parser.py # Парсинг → LLM → схема критериев + API 
- - country_filter.py # Фильтрация стран 
- - safety_monitor.py # Проверка безопасности (LLM + новости) 
- data/ 
- - countries.json # База стран


## Установка

# Создать виртуальное окружение
python3 -m venv myenv
source myenv/bin/activate

# Установить зависимости
pip install -r requirements.txt
Настройка
Скопируйте .env.example в .env
Заполните переменные:
PROXYAPI=https://api.proxyapi.ru/openai/v1
OPENAI_API_KEY=your-api-key

# Запуск
python -m uvicorn services.research_parser:app --reload
Откройте http://localhost:8000

# API Endpoints
Метод	Путь	Описание
GET	/	Главная страница с формой
GET	/form-schema	Схема формы для фронтенда
GET	/criteria-schema	Схема критериев
POST	/analyze-intent	Анализ свободного текста
POST	/search	Поиск стран по критериям
GET	/safety/{country}	Проверка безопасности страны

# Примеры запросов
# Поиск стран
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"climate": "warm", "travel_type": "beach", "budget": 1000}'

# Анализ текста
curl -X POST http://localhost:8000/analyze-intent \
  -H "Content-Type: application/json" \
  -d '{"text": "Хочу тепло, без визы, бюджет 1500"}'

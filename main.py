"""
AI Tourism - главный модуль
"""

from services.research_parser import run_research


def main():
    print("AI Tourism System")
    print("=" * 50)
    
    # Запуск Research
    run_research()


if __name__ == "__main__":
    main()
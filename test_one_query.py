from collectors.link_collector import collect_links
from collectors.card_parser import parse_organization

city = "Москва"
query = "монтаж автополива"

links = collect_links(city, query, headless=False, koef=0.5)  # headless=False, чтобы видеть браузер

print(f"Найдено ссылок: {len(links)}")
for url in links[:5]:  # покажем первые 5
    print(url)

# Парсинг первых 3 карточек для примера
for i, url in enumerate(links[:3]):
    print(f"\n--- Карточка {i+1}: {url}")
    data = parse_organization(url, headless=True)  # можно headless=True для фона
    if data:
        for key, value in data.items():
            print(f"{key}: {value}")
    else:
        print("Не удалось распарсить")
import os
import csv
import itertools
import threading
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from collectors.link_collector import collect_links
import time

# --- Конфигурация ---
CITIES_FILE = "cities.txt"
KEYWORDS_FILE = "keywords.txt"
PROXIES_FILE = "proxies.txt"          # опционально
OUTPUT_LINKS = "data/links_raw.csv"
PROGRESS_FILE = "data/progress_links.txt"
MAX_WORKERS = 3 # потоков для сбора ссылок
HEADLESS = True
KOEF = 0.5           # пауза между прокрутками

# --- Загрузка списков ---
with open(CITIES_FILE, encoding='utf-8') as f:
    cities = [line.strip() for line in f if line.strip()]
with open(KEYWORDS_FILE, encoding='utf-8') as f:
    keywords = [line.strip() for line in f if line.strip()]

city_stats = {city: {"total": 0, "success": 0, "failed": 0, "links": 0} for city in cities}
current_city = None
lock_stats = threading.Lock()

# Прокси (если есть)
proxies = []
if os.path.exists(PROXIES_FILE):
    with open(PROXIES_FILE, encoding='utf-8') as f:
        proxies = [line.strip() for line in f if line.strip()]
proxy_cycle = itertools.cycle(proxies) if proxies else None

# --- Загрузка прогресса ---
processed = set()
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, encoding='utf-8') as f:
        for line in f:
            processed.add(line.strip())

# --- Потокобезопасная запись ---
lock = threading.Lock()
def write_links(city, query, links):
    with lock:
        with open(OUTPUT_LINKS, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for url in links:
                writer.writerow([city, query, url])
        with open(PROGRESS_FILE, 'a', encoding='utf-8') as pf:
            pf.write(f"{city}|{query}\n")

# --- Функция обработки одного запроса ---
def process_query(city, query):
    global current_city
    key = f"{city}|{query}"

    # Для вывода при смене города
    with lock_stats:
        if current_city != city:
            if current_city is not None:
                # Выводим итоги по предыдущему городу
                stats = city_stats[current_city]
                print(f"\n=== ГОРОД {current_city} обработан ===\n"
                      f"  Всего запросов: {stats['total']}\n"
                      f"  Успешно: {stats['success']}\n"
                      f"  Ошибок: {stats['failed']}\n"
                      f"  Собрано ссылок: {stats['links']}\n")
            current_city = city
        # Увеличиваем общее число запросов для города
        city_stats[city]["total"] += 1

    key = f"{city}|{query}"
    if key in processed:
        print(f"✓ Уже обработано: {key}")
        return
    print(f"→ Обрабатывается: {key}")
    proxy = next(proxy_cycle) if proxy_cycle else None
    links = collect_links(city, query, proxy=proxy, headless=HEADLESS, koef=KOEF)
    if links:
        write_links(city, query, links)
        print(f"  ✓ Найдено ссылок: {len(links)}")
    else:
        print(f"  ⚠ Нет ссылок для {key}")

    time.sleep(1)  # Даём системе время на завершение процессов
    gc.collect()

    # В месте, где запрос успешно завершён (после записи результатов):
    with lock_stats:
        city_stats[city]["success"] += 1
        city_stats[city]["links"] += len(links)  # links - список ссылок

    # В месте, где после всех попыток ошибка:
    with lock_stats:
        city_stats[city]["failed"] += 1

# --- Создание файла с заголовком, если его нет ---
os.makedirs("data", exist_ok=True)
if not os.path.exists(OUTPUT_LINKS):
    with open(OUTPUT_LINKS, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['city', 'query', 'url'])

# --- Запуск пула потоков ---
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = []
    for city in cities:
        for kw in keywords:
            futures.append(executor.submit(process_query, city, kw))

    for future in as_completed(futures):
        try:
            future.result()
        except Exception as e:
            print(f"[ERROR] в потоке: {e}")
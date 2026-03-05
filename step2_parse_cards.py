import os
import csv
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from collectors.card_parser import parse_organization

# --- Конфигурация ---
LINKS_FILE = "data/links_raw.csv"
ORGS_FILE = "data/organizations.csv"
QUERIES_FILE = "data/organization_queries.csv"
PARSED_URLS_FILE = "data/parsed_urls.txt"
MAX_WORKERS = 10
HEADLESS = True

# --- Сбор уникальных URL с привязкой к запросам ---
url_to_queries = defaultdict(list)  # url -> список (city, query)
with open(LINKS_FILE, encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)  # пропускаем заголовок
    for row in reader:
        if len(row) >= 3:
            city, query, url = row[0], row[1], row[2]
            url_to_queries[url].append((city, query))

print(f"Всего уникальных URL: {len(url_to_queries)}")

# --- Загрузка уже обработанных URL ---
processed_urls = set()
if os.path.exists(PARSED_URLS_FILE):
    with open(PARSED_URLS_FILE, encoding='utf-8') as f:
        for line in f:
            processed_urls.add(line.strip())

# --- Потокобезопасная запись ---
lock = threading.Lock()

def init_csv():
    if not os.path.exists(ORGS_FILE):
        with open(ORGS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['org_id', 'name', 'rating', 'address', 'coordinates',
                             'phones', 'email', 'website', 'metro', 'working_hours', 'social'])
    if not os.path.exists(QUERIES_FILE):
        with open(QUERIES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['org_id', 'city', 'query', 'url'])

init_csv()

# --- Функция парсинга одной карточки ---
def parse_and_save(url, city_query_list):
    if url in processed_urls:
        return
    data = parse_organization(url, headless=HEADLESS)
    if data and data.get('org_id'):
        org_id = data['org_id']
        with lock:
            # Запись в organizations.csv
            with open(ORGS_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    org_id,
                    data.get('name', ''),
                    data.get('rating', ''),
                    data.get('address', ''),
                    data.get('coordinates', ''),
                    data.get('phones', ''),
                    data.get('email', ''),
                    data.get('website', ''),
                    data.get('metro', ''),
                    data.get('working_hours', ''),
                    data.get('social', '')
                ])
            # Запись связей
            with open(QUERIES_FILE, 'a', newline='', encoding='utf-8') as fq:
                writerq = csv.writer(fq)
                for city, query in city_query_list:
                    writerq.writerow([org_id, city, query, url])
            # Помечаем URL как обработанный
            with open(PARSED_URLS_FILE, 'a', encoding='utf-8') as pf:
                pf.write(url + '\n')
        print(f"✓ Спарсено: {org_id} - {data.get('name')}")
    else:
        print(f"✗ Не удалось спарсить {url}")

# --- Очередь URL для парсинга ---
urls_to_parse = [(url, qlist) for url, qlist in url_to_queries.items() if url not in processed_urls]
print(f"Осталось спарсить URL: {len(urls_to_parse)}")

# --- Многопоточный запуск ---
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(parse_and_save, url, qlist) for url, qlist in urls_to_parse]
    for future in as_completed(futures):
        try:
            future.result()
        except Exception as e:
            print(f"[ERROR] в потоке парсинга: {e}")
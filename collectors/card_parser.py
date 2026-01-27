import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def parse_organization(url, headless=True, proxy=None):
    """
    Парсит карточку организации по URL.
    Возвращает словарь с данными или None в случае ошибки.
    """
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    data = {}

    try:
        driver.get(url)
        time.sleep(2)  # Ждём загрузку динамического контента

        # Иногда страница может редиректить — берём финальный URL
        final_url = driver.current_url
        soup = BeautifulSoup(driver.page_source, "lxml")

        # ID организации (берём из URL)
        parts = final_url.split('/')
        if len(parts) > 6:
            data['org_id'] = parts[6]
        else:
            data['org_id'] = ''

        # Название
        name_tag = soup.find("h1", class_="orgpage-header-view__header")
        data['name'] = name_tag.get_text(strip=True) if name_tag else ''

        category = ''
        breadcrumbs_div = soup.select_one("div.business-card-view__breadcrumbs")
        if breadcrumbs_div:
            # Ищем все ссылки с классом breadcrumbs-view__breadcrumb внутри контейнера
            links = breadcrumbs_div.find_all("a", class_="breadcrumbs-view__breadcrumb")
            if links:
                # Берём последнюю ссылку — это и есть категория
                category_tag = links[-1]
                category = category_tag.get_text(strip=True)
        data['category'] = category

        # Рейтинг
        rating_tag = soup.find("span", class_="business-rating-badge-view__rating-text")
        data['rating'] = rating_tag.get_text(strip=True) if rating_tag else ''

        # Адрес
        addr_tag = soup.find("a", class_="business-contacts-view__address-link")
        data['address'] = addr_tag.get_text(strip=True) if addr_tag else ''

        # Координаты из URL
        coord_match = re.search(r'll=([\d.,-]+)', final_url)
        data['coordinates'] = coord_match.group(1) if coord_match else ''

        # Телефоны
        phone_div = soup.find("div", class_="orgpage-phones-view__phone-number")
        data['phones'] = phone_div.get_text(strip=True) if phone_div else ''

        # Email
        email_span = soup.find("span", class_="business-urls-view__text")
        data['email'] = email_span.get_text(strip=True) if email_span else ''

        # Сайт
        site_link = soup.find("a", class_="business-urls-view__link")
        data['website'] = site_link.get('href') if site_link else ''

        # Метро
        metro_div = soup.find("div", class_="masstransit-stops-view _type_metro _clickable")
        if metro_div:
            stations = metro_div.find_all("a")
            data['metro'] = ', '.join([s.get_text(strip=True) for s in stations])
        else:
            data['metro'] = ''

        # Режим работы
        hours_meta = soup.find_all("meta", {"itemprop": "openingHours"})
        if hours_meta:
            hours = [h.get('content') for h in hours_meta if h.get('content')]
            data['working_hours'] = '; '.join(hours)
        else:
            data['working_hours'] = ''

        # Социальные сети (WhatsApp, Telegram и др.)
        social_links = []
        social_div = soup.find("div", class_="business-contacts-view__social-links")
        if social_div:
            links = social_div.find_all("a")
            for a in links:
                href = a.get('href')
                label = a.get('aria-label')
                if href:
                    social_links.append(f"{label}:{href}" if label else href)
        data['social'] = '; '.join(social_links)

    except Exception as e:
        print(f"[ERROR] parse_organization {url}: {e}")
        data = None
    finally:
        driver.quit()

    return data
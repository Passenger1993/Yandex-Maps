import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import traceback
import re

from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException

def collect_links(city, query, proxy=None, headless=True, koef=0.5, timeout=60):
    """
    Собирает все ссылки на карточки организаций по запросу 'city query' в Яндекс Картах.
    Возвращает список уникальных URL.
    """
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    # Дополнительные опции для стабильности
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)
    actions = ActionChains(driver)
    links = set()

    try:
        driver.get("https://yandex.ru/maps")
        time.sleep(random.uniform(2, 3))

        # Ввод запроса
        search_input = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.TAG_NAME, "input"))
        )
        search_input.clear()
        search_input.send_keys(f"{city} {query}")
        search_input.send_keys(Keys.RETURN)
        time.sleep(random.uniform(2, 3))

        # Ожидаем появления хотя бы одной ссылки на организацию
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/org/']"))
        )

        # Прокрутка для загрузки всех элементов (опционально, если нужно больше)
        last_count = 0
        for _ in range(20):  # максимум 20 попыток прокрутки
            # Собираем текущие ссылки
            links_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/org/']")
            current_count = len(links_elements)
            if current_count == last_count:
                break
            last_count = current_count
            # Прокручиваем список
            driver.execute_script("arguments[0].scrollIntoView();", links_elements[-1])
            time.sleep(koef)

        # Извлекаем уникальные ссылки
        links = set()
        for elem in links_elements:
            href = elem.get_attribute('href')
            if href and not re.search(r'/(reviews|gallery|photos|discovery)/', href):
                full_url = "https://yandex.ru" + href if href.startswith('/') else href
                links.add(full_url)
    except Exception as e:
        raise  # или return []
    finally:
        if driver:
            driver.quit()  # Это гарантированно закроет браузер
            print(f"[DEBUG] Драйвер для {city} {query} закрыт")

    return list(links)
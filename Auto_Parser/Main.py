from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from colorama import *
from Write_Data import main_for_two_file

# Инициализация colorama
init()

DATA = set()
num_of_page = 1
URL = "https://yandex.ru/maps"

def get_links(source):
    soup = BeautifulSoup(source, "lxml")
    many_links = soup.find("ul", class_="search-list-view__list").find_all(
        "a", class_="link-overlay"
    )
    print(str(len(DATA)) + " - сколько ссылок на данный момент в txt-файле")
    for i in many_links:
        try:
            text = i.get("href")
            res_link = "https://yandex.ru" + text
            if not("/maps/discovery/" in res_link):
                DATA.add(res_link)
        except:
            pass

def save_in_txt(data):
    with open("links.txt", 'w', encoding='utf-8') as file:
        for line in data:
            file.write(line + "\n")

def scrolling_of_page(data_one, data_two):
    for _ in range(7):
        try:
            driver.get(URL)
            sleep(1)

            # Ввод запроса
            search_input = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.TAG_NAME, "input"))
            )
            search_input.send_keys(data_one)
            search_input.send_keys(" " + data_two)
            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.TAG_NAME, "button"))
            ).click()
            sleep(1.5)

            content_div = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "search-list-view__content"))
            )
            first_child = content_div.find_element(By.XPATH, "./*")
            actions.click(first_child).perform()
            sleep(1)

            len_mass_li = len(driver.find_element(By.CLASS_NAME, "search-list-view__list").find_elements(By.TAG_NAME, "li")) # количество загрузившихся карточек

            return len_mass_li
        except:
            pass # место для логов

    print(f"Ошибка при загрузке страницы или при попытке найти по запросу {data_one} {data_two}, проверьте интернет-соединение или браузер, и перезапустите программу.")
    driver.quit()
    exit()

def get_data_from_links():
    num_of_keys_down = 0
    print(Fore.MAGENTA + Style.BRIGHT + "Введите город: ", end="")
    city_data = input()
    print(Fore.CYAN + Style.BRIGHT + "Введите что вы хотите найти: ", end="")
    what_data = input()
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Введите коэфицент точности\n(влияет на то, на склько точно спарсятся все ссылки на карточки\nот 0 до 2 (пример - 0, 0.02, 0.7, 1.34), чем ближе к нулю тем быстрее будет парситься,\nно некоторые ссылки на карточки может пропустить,\nчем ближе к 2 тем точнее, но дольше парсится): ", end="")
    koef_data = float(input())

    len_mass_li = scrolling_of_page(city_data, what_data)

    while True:

        # Прокрутка вниз
        try:
            html_scroll = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "scroll__scrollbar-thumb"))
            )
            scroll_origin = ScrollOrigin.from_element(html_scroll)
            for _ in range(10):
                ActionChains(driver).scroll_from_origin(scroll_origin, 0, 1000).perform()
                sleep(koef_data) # задержка для корректной подгрузки
        except:
            if num_of_keys_down == 7:
                print(f"Ошибка при прокуртке страницы, проверьте интернет-соединение или запущенный хром-браузер. НЕ ВЫКЛЮЧАЙТЕ ПРОГРАММУ, она продолжит прасинг.\n"
                      f"Однако не все ссылки на карточки были спаршены. Для полного изъятия данных, после завершения работы скрипта, перезапустите его!")
                break
            num_of_keys_down += 1
            continue

        try:
            get_links(driver.page_source)
        except:
            break

        if len(driver.find_element(By.CLASS_NAME, "search-list-view__list").find_elements(By.TAG_NAME, "li")) > len_mass_li: # сравнивание сколько сейчас карточек, с предыдущим числом
            len_mass_li = len(driver.find_element(By.CLASS_NAME, "search-list-view__list").find_elements(By.TAG_NAME, "li"))
        else:
            break # выход из скролинга

    save_in_txt(DATA)
    print(f"{len(DATA)} - всего найдено ссылок по запросу")
    sleep(1)
    return city_data

def main():
    name_city = get_data_from_links()
    return name_city

if __name__ == "__main__":
    timeheadless = bool(input("Хотите, чтобы программа работала в фоновом режиме? "
                              "(Если да — введите любое слово, если нет — просто нажмите Enter): "))
    parsphotoslogos = bool(input("Хотите, чтобы программа парсила фотки и логотипы? "
                              "(Если да — введите любое слово, если нет — просто нажмите Enter): "))

    options = webdriver.ChromeOptions()
    if timeheadless:
        options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)
    actions = ActionChains(driver)

    city_data = main()

    # полное закрытие браузера
    driver.quit()

    main_for_two_file(city_data, parsphotoslogos)
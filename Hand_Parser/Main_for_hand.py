from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from colorama import *
from Write_Data_for_hand import main_for_two_file

# Инициализация colorama
init()

DATA = set()
num_of_page = 1
URL = "https://yandex.ru/maps"

def get_links(source):
    soup = BeautifulSoup(source, "lxml")
    many_links = soup.find("ul", class_="search-list-view__list").find_all(
        "a", class_="link-overlay" #"search-snippet-view__link-overlay _focusable"
    )
    print(str(len(DATA)) + " - сколько ссылок на данный момент в txt-файле")
    for i in many_links:
        text = i.get("href")
        res_link = text
        if not("/maps/discovery/" in res_link):
            DATA.add(res_link)

    city_data = soup.find('input', class_='input__control _bold').get('value').split()[0]
    return city_data

def save_in_txt(data):
    with open("links.txt", 'w', encoding='utf-8') as file:
        for line in data:
            file.write(line + "\n")

def get_data_from_links():
    city_data = ''

    with open("ym.htm", 'r', encoding='utf-8') as file:
        page_resource = file.read()
        city_data = get_links(page_resource)

    save_in_txt(DATA)
    print(f"{len(DATA)} - всего найдено ссылок по запросу")
    sleep(1)
    return city_data

def main():
    name_city = get_data_from_links()
    return name_city

if __name__ == "__main__":
    parsphotoslogos = bool(input("Хотите, чтобы программа парсила фотки и логотипы? "
                              "(Если да — введите любое слово, если нет — просто нажмите Enter): "))
    city_data = main()

    main_for_two_file(city_data, parsphotoslogos)
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.keys import Keys
import requests
from bs4 import BeautifulSoup
import time
import datetime
import random

time.sleep(5) 

driver_path = '/usr/local/bin/geckodriver'


url = os.environ.get('URL')
db_url = f"postgresql://{os.environ.get('POSTGRES_USER')}:{os.environ.get('POSTGRES_PASSWORD')}@{os.environ.get('DB_HOST')}/{os.environ.get('POSTGRES_DB')}"

connection = create_engine(db_url)
Session = sessionmaker(bind=connection)
session = Session()
Base = declarative_base()

# Модель таблиці
class Car(Base):
    __tablename__ = 'cars'

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True)
    title = Column(String)
    price_usd = Column(Integer)
    odometer = Column(Integer)
    username = Column(String)
    phone_number = Column(String)
    image_url = Column(String)
    images_count = Column(Integer)
    number = Column(String)
    vin = Column(String)
    datetime_found = Column(DateTime, default=datetime.datetime.utcnow)

# Створення БД, якщо вона порожня
Base.metadata.create_all(connection)

time.sleep(5) 

while True:
    # Запит сторінки
    request_pages = requests.get(url)
    bs_pages = BeautifulSoup(request_pages.text, "html.parser")

    all_links_on_page = bs_pages.find_all("a", class_="address")
    n = 1
    # Перебір посилань на сторінці
    for link in all_links_on_page:
        try:
            existing_car = session.query(Car).filter_by(url=link["href"]).first()

            if existing_car is None:
                # Запит інформації про машину
                request_car = requests.get(link["href"])
                bs_car = BeautifulSoup(request_car.text, "html.parser")

                car_title = bs_car.find("h1", class_="head")["title"]
                car_price = int(bs_car.find("div", class_="price_value").find("strong").text.replace('грн', '')[:-2].replace(' ', ''))
                car_odometer = int(bs_car.find("div", class_="base-information bold").find("span", class_="size18").text + '000')

                # Обробка різних варіантів імені продавця
                if bs_car.find("h4", class_="seller_info_name"):
                    car_username = ' '.join(bs_car.find("h4", class_="seller_info_name").find('a').text.split())
                elif bs_car.find("div", class_="seller_info_name grey bold"):
                    car_username = ' '.join(bs_car.find("div", class_="seller_info_name grey bold").text.split())
                else:
                    car_username = ' '.join(bs_car.find("div", class_="seller_info_name bold").text.split())

                # Кілкість зображень
                car_images_count = bs_car.find("div", class_="count-photo left").find("span", class_="mhide").text.split()[-1]

                # Номер авто
                if bs_car.find("span", class_="state-num"):
                    car_number = bs_car.find("span", class_="state-num").next_element.get_text().replace(" Ми розпізнали держномер авто на фото и перевірили його за реєстрами МВС.", '')
                else:
                    car_number = "Не вказано"

                # Обработка VIN-кода
                if bs_car.find("span", class_="checked_ad label-check"):
                    car_vin = bs_car.find("span", class_="label-vin").next_element.next_element.next_element.text
                elif bs_car.find("span", class_="vin-code"):
                    car_vin = bs_car.find("span", class_="vin-code").text
                else:
                    car_vin = "Не вказано"

                # Номери телефонів
                car_phone_number = []
                firefox_options = Options()
                firefox_options.add_argument("--headless")
                service = Service(driver_path)
                driver = webdriver.Firefox(options=firefox_options, service=service)
                driver.get(link["href"])

                if driver.find_element(By.XPATH, "//a[@class='size14 phone_show_link link-dotted mhide' and text()='показати']"):
                    show_button = driver.find_element(By.XPATH, "//a[@class='size14 phone_show_link link-dotted mhide' and text()='показати']")
                    driver.execute_script("arguments[0].scrollIntoView(true);", show_button)
                    show_button.click()
                    time.sleep(0.5)

                    popup_content = driver.page_source
                    popup_soup = BeautifulSoup(popup_content, 'html.parser')
                    car_phone_numbers = popup_soup.find_all("div", class_="popup-successful-call-desk")

                    for phone in car_phone_numbers:
                        if phone["data-value"] != '':
                            phone = "".join(phone["data-value"].split()).replace("(", "+38").replace(")", "")
                            car_phone_number.append(phone)
                        else:
                            car_phone_number = "Не вказано"
                            break
                    if car_phone_number != "Не вказано":
                        car_phone_number = ", ".join(car_phone_number)
                else:
                    car_phone_number = "Не вказано"
                driver.quit()
                #img url
                car_image_url = bs_car.find("img", class_="outline m-auto")["src"].replace(".jpg", "hd.jpg")

                new_car = Car(
                    url=link["href"],
                    title=car_title,
                    price_usd=car_price,
                    odometer=car_odometer,
                    username=car_username,
                    phone_number=car_phone_number,
                    image_url=car_image_url,
                    images_count=car_images_count,
                    number=car_number,
                    vin=car_vin
                )

                session.add(new_car)
                session.commit()
                driver.quit()
                
            else:
                print("Є у БД")
        except Exception as e:
            print("Авто продано ", link["href"])

    last_page = bs_pages.find("a", class_ = 'page-link js-next disabled')
        # Остання сторінка
    if last_page:
        print("Прогрма завершила сбір даних")
        break
        
    # Наступна сторінка
    url = bs_pages.find("a", class_ = 'page-link js-next')["href"]

    
    time.sleep(random.uniform(0.5, 1))

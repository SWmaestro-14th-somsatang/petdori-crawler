# 견종 목록을 크롤링하고 바로 DB에 저장

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import pymysql
import os

load_dotenv()
DOG_TYPE_CRAWLING_URL = os.getenv("DOG_TYPE_CRAWLING_URL")


def time_wait(num, code="key"):
    try:
        wait = WebDriverWait(driver, num).until(
            EC.presence_of_element_located((By.ID, code)))
    except:
        print(code, '태그를 찾지 못하였습니다.')
        driver.quit()
    return wait


crawled_data = []

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get(DOG_TYPE_CRAWLING_URL)

# 웹페이지가 로드될 때까지 10초 대기
time_wait(10)

while True:
    div = driver.find_element(By.CLASS_NAME, "in")
    dog_list = div.find_elements(By.CLASS_NAME, "me02_list")

    for dog_info in dog_list:
        content = dog_info.find_element(By.CLASS_NAME, "me02_cont")
        kind = content.find_element(By.CLASS_NAME, "kind")
        dog_type_name = kind.text

        if dog_type_name.find("("):
            parentheses_index = dog_type_name.index("(")
            dog_type_name = dog_type_name[:parentheses_index - 1]

        crawled_data.append(dog_type_name.strip())

    current_page_list = driver.find_element(By.TAG_NAME, "tr")\
        .find_elements(By.TAG_NAME, "td")
    next_page_li_tag = None

    for i in range(1, len(current_page_list)):
         now_page = current_page_list[i]
         td_tag_class_name = now_page.get_attribute("class")

         if td_tag_class_name == "over":
            if i != len(current_page_list) - 1:
                next_page_li_tag = current_page_list[i + 1]
            break

    if next_page_li_tag.get_attribute("class") == "next_none":
        break

    next_page_li_tag.click()

crawled_data.sort()

DB_HOST = os.getenv("DB_HOST")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

conn = pymysql.connect(
    host=DB_HOST,
    user=DB_USERNAME,
    password=DB_PASSWORD,
    db=DB_NAME,
    charset='utf8'
)
cur = conn.cursor()

for type_name in crawled_data:
    query = "INSERT INTO dog_type (type_name, created_date, modified_date) " \
                    "VALUES (%s, now(), now())"
    cur.execute(query, (type_name))

conn.commit()
conn.close()

print("끝")

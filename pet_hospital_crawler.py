# 동물병원 정보들을 크롤링해 csv로 저장(병원명, 주소값들)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import csv
import os

load_dotenv()
HOSPITAL_CRAWLING_URL = os.getenv("HOSPITAL_CRAWLING_URL")


def time_wait(num, code="searchCoNm"):
    try:
        wait = WebDriverWait(driver, num).until(
            EC.presence_of_element_located((By.ID, code)))
    except:
        print(code, '태그를 찾지 못하였습니다.')
        driver.quit()
    return wait


crawled_data = []

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get(HOSPITAL_CRAWLING_URL)

# 웹페이지가 로드될 때까지 10초 대기
time_wait(10)

while True:
    table = driver.find_element(By.TAG_NAME, "table")
    t_body = table.find_element(By.TAG_NAME, "tbody")
    rows = t_body.find_elements(By.TAG_NAME, "tr")

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        hospital_name, hospital_address = cols[1].text, cols[3].text
        crawled_data.append({
            "hospital_name": hospital_name,
            "hospital_address": hospital_address,
        })

    current_page_list = driver.find_element(By.CLASS_NAME, "paging")\
        .find_elements(By.TAG_NAME, "li")
    next_page_li_tag = None

    for i in range(len(current_page_list)):
        a_tag_content = current_page_list[i].find_element(By.TAG_NAME, "a")
        a_tag_class_name = a_tag_content.get_attribute("class")

        if a_tag_class_name == "active":
            if i != len(current_page_list) - 1:
                next_page_li_tag = current_page_list[i + 1]
            break

    if not next_page_li_tag:
        break

    next_page_li_tag.click()

csv_file_path = "hospital_data.csv"

# CSV 파일을 쓰기 모드로 열고 데이터를 저장
with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
    # CSV writer 객체 생성
    writer = csv.writer(file)

    # CSV 파일의 첫 번째 행에 열 이름을 쓰기
    writer.writerow(["hospital_name", "hospital_address"])

    # 각 병원 데이터를 CSV 파일에 쓰기
    for data in crawled_data:
        writer.writerow([data["hospital_name"], data["hospital_address"]])

print("저장 완료")

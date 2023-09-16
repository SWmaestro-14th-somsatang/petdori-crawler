# 동물병원 주소값, 운영시간 크롤링해 csv로 저장
# 동물병원 이름들을 검색하고, 검색해서 나오는 주소와 운영시간들을 크롤링하고
# 주소들을 바탕으로 위도 경도를 얻어옴(오픈된 api 사용)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from time import sleep
import requests
import csv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")
LAT_LONG_SEARCH_URL = os.getenv("LAT_LONG_SEARCH_URL")
ADDRESS_CRAWLING_URL = os.getenv("ADDRESS_CRAWLING_URL")


def time_wait(num, code="search.keyword.query"):
    try:
        wait = WebDriverWait(driver, num).until(
            EC.presence_of_element_located((By.ID, code)))
    except:
        print(code, '태그를 찾지 못하였습니다.')
        driver.quit()
    return wait


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get(ADDRESS_CRAWLING_URL)

# 웹페이지가 로드될 때까지 10초 대기
time_wait(10)

# 병원명 기반으로 주소, 운영시간 모아오기
crawled_address = set()
crawled_hospital_info = []
csv_file_path = "hospital_data.csv"

try:
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        # 첫 번째 행은 열 이름이므로 스킵
        next(reader)

        for row in reader:
            hospital_name = row[0]

            if not hospital_name:
                continue
            # 동물병원 이름 전처리
            if hospital_name.startswith("(주)"):
                hospital_name = hospital_name[3:]
            if hospital_name.find("(") != -1:
                hospital_name = hospital_name[:hospital_name.find("(")]
            if hospital_name.find("「") != -1:
                hospital_name = hospital_name[:hospital_name.find("(")]

            search_input = driver.find_element(By.ID, 'search.keyword.query')
            search_input.clear()
            search_input.send_keys(hospital_name)
            search_input.send_keys(Keys.ENTER)

            sleep(1)

            search_place_list = driver.find_element(By.ID, 'info.search.place.list')
            search_places = search_place_list.find_elements(By.TAG_NAME, "li")

            if not search_places:
                continue

            for i in range(len(search_places)):
                try:
                    hospital_name = search_places[i].find_element(By.CLASS_NAME, "head_item")\
                        .find_element(By.CLASS_NAME, "tit_name")\
                        .find_elements(By.TAG_NAME, "a")[1]\
                        .get_attribute("title")

                    hospital_address = search_places[i].find_element(By.CLASS_NAME, "info_item")\
                        .find_element(By.CLASS_NAME, "addr")\
                        .find_elements(By.TAG_NAME, "p")[0]\
                        .get_attribute("title")

                    hospital_open_hour = search_places[i].find_element(By.CLASS_NAME, "info_item")\
                        .find_element(By.CLASS_NAME, "openhour")\
                        .find_element(By.CLASS_NAME, "periodWarp")\
                        .find_element(By.TAG_NAME, "a").text

                    if hospital_address not in crawled_address:
                        crawled_address.add(hospital_address)
                        crawled_hospital_info.append({
                            "hospital_name": hospital_name,
                            "hospital_address": hospital_address,
                            "hospital_open_hour": hospital_open_hour
                        })
                except Exception as e:
                    continue

except FileNotFoundError:
    print(f"CSV 파일 '{csv_file_path}'를 찾을 수 없습니다.")
    exit()
except Exception as e:
    print(f"오류 발생: {e}")
    exit()

# csv로 저장 - (백업용), (병원명, 주소, 운영시간)
csv_file_path = "new_hospital_data - middle.csv"

# CSV 파일을 쓰기 모드로 열고 데이터를 저장
with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
    # CSV writer 객체 생성
    writer = csv.writer(file)

    # CSV 파일의 첫 번째 행에 열 이름을 쓰기
    writer.writerow(["hospital_name", "hospital_address", "hospital_open_hour"])

    # 각 병원 데이터를 CSV 파일에 쓰기
    for data in crawled_hospital_info:
        writer.writerow([
            data["hospital_name"],
            data["hospital_address"],
            data["hospital_open_hour"],
        ])

print("저장 완료 - 1")

# 주소 기반으로 위경도 받아오기
new_hospital_data = []
for hospital_info in crawled_hospital_info:
    hospital_name = hospital_info["hospital_name"]
    hospital_address = hospital_info["hospital_address"]
    hospital_open_hour = hospital_info["hospital_open_hour"]

    res = requests.get(LAT_LONG_SEARCH_URL + hospital_address,
                   headers={"Authorization": f"KakaoAK {API_KEY}"}).json()

    # 위경도를 못 구한 경우
    if 'documents' not in res or not res['documents']:
        continue

    lat, long = res['documents'][0]['y'], res['documents'][0]['x']

    new_hospital_data.append({
        "hospital_name": hospital_name,
        "hospital_address": hospital_address,
        "hospital_open_hour": hospital_open_hour,
        "latitude": lat,
        "longitude": long
    })

    print(f"{hospital_name}에 대한 위도 경도 구하기 완료")

# csv로 저장 - (병원명, 주소, 운영시간, 위도, 경도)
csv_file_path = "new_hospital_data.csv"

# CSV 파일을 쓰기 모드로 열고 데이터를 저장
with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
    # CSV writer 객체 생성
    writer = csv.writer(file)

    # CSV 파일의 첫 번째 행에 열 이름을 쓰기
    writer.writerow(["hospital_name", "hospital_address", "hospital_open_hour", "latitude", "longitude"])

    # 각 병원 데이터를 CSV 파일에 쓰기
    for data in new_hospital_data:
        writer.writerow([
            data["hospital_name"],
            data["hospital_address"],
            data["hospital_open_hour"],
            data["latitude"],
            data["longitude"]
        ])

print("저장 완료 - 2")

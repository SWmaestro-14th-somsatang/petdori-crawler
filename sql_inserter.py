# pet_hospital_lat_long_crawler를 통해 만들어진 csv파일을 기반으로
# mysql db에 동물병원정보, 영업시간정보를 주입

from dotenv import load_dotenv
import pymysql
import csv
import os

load_dotenv()

day_of_the_week_dict = {
    "일": ["SUN", 6],
    "월": ["MON", 0],
    "화": ["TUE", 1],
    "수": ["WED", 2],
    "목": ["THU", 3],
    "금": ["FRI", 4],
    "토": ["SAT", 5]
}

day_of_the_week_list = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

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

csv_file_path = "new_hospital_data.csv"

try:
    # CSV 파일을 읽기 모드로 열기
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        # CSV reader 객체 생성
        reader = csv.reader(file)

        # 첫 번째 행은 열 이름이므로 스킵
        next(reader)

        # 동물병원 데이터를 반복해서 출력
        for row in reader:
            hospital_name = row[0].strip()
            hospital_address = row[1].strip()
            hospital_open_hour = row[2].strip()
            latitude = row[3].strip()
            longitude = row[4].strip()

            # 시설 정보 저장
            query = f"INSERT INTO pet_facility (name, pet_facility_type_id, address, location, created_date, modified_date) " \
                    f"VALUES('{hospital_name}', 1, '{hospital_address}', POINT{longitude, latitude}, now(), now())"
            cur.execute(query)

            # 운영시간정보도 있다면, 운영시간정보도 저장한다
            if hospital_open_hour:
                # 앞서 저장한 시설정보의 id가져오기
                cur.execute(f"select id from pet_facility where address='{hospital_address}'")
                res = cur.fetchone()
                pet_facility_id = res[0]

                if hospital_open_hour.startswith("영업시간 "):
                    hospital_open_hour = hospital_open_hour[5:]

                sliced_hour_info = hospital_open_hour.split()

                if len(sliced_hour_info) == 1:
                    continue

                # day_info : "매일", "토~일", "금", "월,화,수,금" 과 같은 형태
                day_info = sliced_hour_info[0]
                open_hour, close_hour = sliced_hour_info[1], sliced_hour_info[3]

                if day_info == "2023년":
                    continue

                query = "INSERT INTO pet_facility_operating_hour (pet_facility_id, day_of_the_week, open_hour, close_hour, created_date, modified_date)"\
                            + "VALUES('%s', %s, %s, %s, now(), now())"

                if day_info == "매일":
                    for key in day_of_the_week_dict.keys():
                        day_of_the_week = day_of_the_week_dict[key][0]
                        cur.execute(query, (pet_facility_id, day_of_the_week, open_hour, close_hour))
                    continue
                # "금" 이런 것들
                if len(day_info) == 1:
                    day_of_the_week = day_of_the_week_dict[day_info][0]
                    cur.execute(query, (pet_facility_id, day_of_the_week, open_hour, close_hour))
                    continue
                # "월,화,수" 이런 것들
                if day_info.find(",") != -1:
                    for d in day_info.split(","):
                        day_of_the_week = day_of_the_week_dict[d][0]
                        cur.execute(query, (pet_facility_id, day_of_the_week, open_hour, close_hour))
                    continue
                # "월~토" 이런 것들
                if day_info.find("~") != -1:
                    start, end = day_info.split("~")
                    start_index, end_index = day_of_the_week_dict[start][1], day_of_the_week_dict[end][1]
                    for day_of_the_week in day_of_the_week_list[start_index:end_index + 1]:
                        cur.execute(query, (pet_facility_id, day_of_the_week, open_hour, close_hour))
                    continue

    conn.commit()
    conn.close()
    print("끝")

except FileNotFoundError:
    print(f"CSV 파일 '{csv_file_path}'를 찾을 수 없습니다.")
except Exception as e:
    print(f"오류 발생: {e}")
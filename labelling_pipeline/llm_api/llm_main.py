import psycopg2
from datetime import datetime
from problem_processor import process_math_problem
from dotenv import load_dotenv
import os
import json

# 환경 변수 로드
load_dotenv(dotenv_path="../pipeline/.env", override=True)

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# PostgreSQL 연결 설정
DB_CONFIG = {
    "dbname": POSTGRES_DB,
    "user": POSTGRES_USER,
    "password": POSTGRES_PASSWORD,
    "host": POSTGRES_HOST,
    "port": POSTGRES_PORT,
}

# 로드맵 파일 경로 설정
ROADMAP_FILES = {
    "수와 연산": r"D:/programming/python/chunjae/finalproject/kst_pipeline/Preprocessing/roadmap/01_num_cal.json",
    "변화와 관계": r"D:/programming/python/chunjae/finalproject/kst_pipeline/Preprocessing/roadmap/02_change_of_relationship.json",
    "도형과 측정": r"D:/programming/python/chunjae/finalproject/kst_pipeline/Preprocessing/roadmap/03_shape_meas.json",
    "자료와 가능성": r"D:/programming/python/chunjae/finalproject/kst_pipeline/Preprocessing/roadmap/04_data_and_possibility.json",
}


def load_roadmap(category):
    """로드맵 JSON 파일 로드"""
    file_path = ROADMAP_FILES.get(category)
    if not file_path:
        raise ValueError(f"로드맵 파일 경로를 찾을 수 없습니다: {category}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_to_db(file_name, category_label, leaf_label):
    """결과를 PostgreSQL에 저장 (psycopg2 사용)"""
    try:
        print(
            f"[DEBUG] 데이터베이스에 저장 중... (파일: {file_name}, 대분류: {category_label}, 최하위분류: {leaf_label})"
        )

        # PostgreSQL 연결
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # FileRecord 찾기
        cur.execute(
            "SELECT id FROM upload_filerecord WHERE file_name = %s;", (file_name,)
        )
        file_record = cur.fetchone()

        # LabellingResult 생성
        file_record_id = file_record[0]
        cur.execute(
            """ 
            INSERT INTO upload_labellingresult (file_record_id, category_label, leaf_label, processed_at)
            VALUES (%s, %s, %s, %s);
        """,
            (file_record_id, category_label, leaf_label, datetime.now()),
        )

        conn.commit()

        print(
            f"[INFO] 저장 성공: {file_name}, 라벨링 결과: {category_label}, {leaf_label}"
        )

        cur.close()
        conn.close()

    except Exception as e:
        print(f"[ERROR] 저장 실패: {e}")
        raise e  # 에러를 상위 호출 함수로 전달


def process_multiple_problems(file_name, processed_data):
    """문제 처리 및 결과 출력"""
    if not processed_data or "text" not in processed_data:
        raise ValueError("전처리된 데이터에 문제 텍스트가 없습니다.")

    question_text = processed_data["text"]

    if not question_text:
        raise ValueError("문제 텍스트가 비어있습니다.")

    print(f"문제 텍스트: {question_text}")

    try:
        # 로드맵 파일 로드
        category_map = {category: load_roadmap(category) for category in ROADMAP_FILES}

        # 문제 처리
        category, leaf_category, category_time, leaf_time = process_math_problem(
            problem_text=question_text,
            category_map=category_map,
            model="gpt-4o",  # 기본 모델을 "gpt-4o"로 설정
        )

        # 처리 결과 출력
        print(f"[DEBUG] 처리 결과:")
        print(f"  파일 이름: {file_name}")
        print(f"  대분류: {category}")
        print(f"  최하위 분류: {leaf_category}")
        print(f"  대분류 추출 시간: {category_time}")
        print(f"  최하위 분류 추출 시간: {leaf_time}")

        return file_name, category, leaf_category, category_time, leaf_time

        # DB 저장 대신 출력으로 대체
        # save_to_db(file_name, category, leaf_category)

    except Exception as e:
        print(f"[ERROR] 문제 처리 실패: {e}")
        raise e  # 예외를 상위 호출 함수로 전달

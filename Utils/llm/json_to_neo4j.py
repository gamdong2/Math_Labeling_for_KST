import json
import os
import openai
import boto3
import pickle
from neo4j import GraphDatabase
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# Neo4j 연결 설정
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

# S3 연결 설정
aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
s3_bucket = os.getenv("S3_BUCKET_NAME")
region_name = os.getenv("AWS_REGION")

# OpenAI API 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# 클라이언트 및 세션 생성
s3_client = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name,
)
driver = GraphDatabase.driver(uri, auth=(username, password))
session = driver.session()


# 벡터 생성 함수 (OpenAI API 사용)
def generate_vector(text):
    response = openai.Embedding.create(model="text-embedding-ada-002", input=text)
    return response["data"][0]["embedding"]


# 벡터 파일 저장 함수
def save_vector_to_file(name, vector):
    vector_path = f"/tmp/vectors/{name.replace(' ', '_')}.pkl"  # 공백을 밑줄로 교체
    os.makedirs("/tmp/vectors", exist_ok=True)
    with open(vector_path, "wb") as f:
        pickle.dump(vector, f)
    return vector_path


# 노드 생성 및 관계 설정 함수
def create_node_and_relationship(
    name, parent_name=None, node_type=None, vector_path=None
):
    node_type = node_type
    # 노드 생성
    query = f"""
    MERGE (n:{node_type} {{name: $name}})
    """
    if vector_path:  # 벡터 경로가 있을 경우 추가 속성 설정
        query += """
        SET n.vector_path = $vector_path
        """
    session.run(query, name=name, vector_path=vector_path)
    print(f"Node created: {name} ({node_type})")

    # 부모 노드와의 관계 설정
    if parent_name:
        query_relationship = """
        MATCH (p {name: $parent_name})
        MATCH (n {name: $name})
        MERGE (p)-[:HAS_CHILD]->(n)
        """
        session.run(query_relationship, name=name, parent_name=parent_name)
        print(f"Relationship created: {parent_name} -> {name}")


# JSON 데이터 처리 함수 (벡터 추가 포함)
def process_json_data(data, parent_name=None, node_type="Category"):
    for key, value in data.items():
        if (
            isinstance(value, dict) and "name" in value
        ):  # 값이 dict이며 'name' 키가 존재할 경우
            item_name = value["name"]
            # 벡터 생성 후 파일에 저장
            vector = generate_vector(item_name)
            vector_path = save_vector_to_file(item_name, vector)

            # 노드 및 관계 생성
            create_node_and_relationship(
                item_name,
                parent_name=parent_name,
                node_type=node_type,
                vector_path=vector_path,
            )

            # 자식 항목 처리
            if "children" in value:
                process_json_data(
                    value["children"], parent_name=item_name, node_type="Branch"
                )
        elif isinstance(value, str):  # 값이 문자열일 경우 (Leaf 노드)
            # 벡터 생성 후 파일에 저장
            vector = generate_vector(value)
            vector_path = save_vector_to_file(value, vector)

            # 노드 및 관계 생성
            create_node_and_relationship(
                value,
                parent_name=parent_name,
                node_type="Leaf",
                vector_path=vector_path,
            )


# JSON 파일 다운로드 및 처리 함수
def process_s3_json(s3_key):
    temp_file = "/tmp/temp_json_file.json"
    s3_client.download_file(s3_bucket, s3_key, temp_file)
    print(f"Downloaded {s3_key} to {temp_file}")
    with open(temp_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        for key, value in data.items():
            category_name = value["name"]

            # 벡터 생성 후 파일에 저장
            vector = generate_vector(category_name)
            vector_path = save_vector_to_file(category_name, vector)

            # 대분류 노드 생성 (벡터 경로 포함)
            create_node_and_relationship(
                category_name, node_type="Category", vector_path=vector_path
            )

            # 자식 항목 처리
            if "children" in value:
                process_json_data(
                    value["children"],
                    parent_name=category_name,
                    node_type="Subcategory",
                )


# S3의 JSON 파일 리스트
s3_keys = [
    "roadmap_2022/01_num_cal.json",
    "roadmap_2022/02_change_of_relationship.json",
    "roadmap_2022/03_shape_meas.json",
    "roadmap_2022/04_data_and_possibility.json",
]

# JSON 파일 처리
try:
    for s3_key in s3_keys:
        process_s3_json(s3_key)
    print("All JSON files have been successfully processed and inserted into Neo4j.")
except Exception as e:
    print(f"Error processing JSON files: {e}")
finally:
    session.close()

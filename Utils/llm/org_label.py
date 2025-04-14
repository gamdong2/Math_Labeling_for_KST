import openai
import os
import numpy as np
from dotenv import load_dotenv
from neo4j import GraphDatabase
import torch
from langchain_ollama import ChatOllama
import json
from langchain_core.runnables import RunnableSequence
from langchain.prompts import PromptTemplate
from langchain_community.llms import OpenAI


# LLM을 사용한 수학 키워드 및 대분류 추출 함수
def extract_category_from_math_problem(text):
    prompt = (
        "다음 수학 문제와 가장 적합한 대분류를 추출하세요. "
        "대분류는 '변화와 관계', '도형과 측정', '자료와 가능성' 중에서 하나를 먼저 확인하고, "
        "그래프나 표와 관련된 문제는 우선적으로 '자료와 가능성'으로 분류하고, "
        "길이, 넓이, 들이, 무게 등의 단위 관련 문제는 '도형과 측정'으로 분류하며, "
        "배열, 규칙, 비율과 관련된 문제는 '변화와 관계'로 분류하세요. "
        "문제가 사칙연산(덧셈, 뺄셈, 곱셈, 나눗셈)과 관련 있다면 '수와 연산'으로 분류하세요. "
        "어디에도 속하지 않으면 '수와 연산'으로 분류하세요.\n"
        f"문제: {text}"
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=150,
        temperature=0.5,
    )

    # 실제 응답 텍스트 추출
    response_text = response.choices[0].message["content"]

    # 작은따옴표 안에 있는 대분류만 추출
    category = response_text.split("'")[1]  # 작은따옴표 안의 내용만 추출

    return category


# 시드 고정
def set_seed(seed=12345):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# 시드 고정 설정
set_seed()


def calculate_similarity(text, leaf):
    query_text = f"Calculate similarity between {text} and {leaf}"

    # GraphRAG를 통해 유사도 계산
    response = rag.search(query_text=query_text, retriever_config={"top_k": 1})
    similarity_score = response.answer[0].get("similarity", 0.0)

    return similarity_score


def filter_nodes_by_category(nodes, category):
    filtered_nodes = [node for node in nodes if category in node["node"]]
    print(f"Filtered Nodes by Category '{category}': {filtered_nodes}")
    return filtered_nodes


def find_similar_nodes_from_graph(text, category, level, similarity_threshold=0.5):
    query_text = f"Find nodes related to {text} in category {category} at level {level}"
    print(f"Query Text: {query_text}")

    try:
        response = rag.search(
            query_text=query_text, category=category, retriever_config={"top_k": 5}
        )
        print(f"Response Type: {type(response)}")
        print(f"Raw Response: {response}")

        # JSON 파싱 및 필터링
        if isinstance(response, str):
            response_data = json.loads(response)
        else:
            response_data = response  # JSON 객체라면 그대로 사용

        if "answer" in response_data:
            matched_nodes = [
                node
                for node in response_data["answer"]
                if node.get("score", 0) >= similarity_threshold
            ]
            filtered_nodes = filter_nodes_by_category(matched_nodes, category)
            print(
                f"Matched Nodes (Filtered by Category '{category}'): {filtered_nodes}"
            )
            return [node["node"] for node in filtered_nodes]
        else:
            print("No 'answer' field in response data.")
            return []

    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


def find_subcategories(text, category):
    best_match = find_similar_nodes_from_graph(text, category, level="Subcategory")
    if best_match:
        return best_match
    print(f"중분류를 찾을 수 없습니다. 대분류: {category}")
    return []


def find_leaf_nodes(text, category_name, similarity_threshold=0.5):
    subcategories = find_subcategories(text, category_name)
    if not subcategories:
        print(f"중분류를 찾을 수 없습니다. 대분류: {category_name}")
        return []

    leaf_nodes = []
    for subcategory in subcategories:
        print(f"중분류 '{subcategory}'에서 하위 노드 탐색 시작")
        items = find_similar_nodes_from_graph(
            text,
            subcategory,
            level="Item",
            similarity_threshold=similarity_threshold,
        )
        if not items:
            print(f"중분류 '{subcategory}'에 연결된 item이 없습니다.")
            continue
        print(f"중분류 '{subcategory}'에 연결된 item: {items}")

        for item in items:
            query = """
                MATCH (i:Item {name: $item})-[:HAS_CHILD]->(ln:Leaf)
                RETURN ln.name AS leaf
            """
            with driver.session() as session:
                result = session.run(query, item=item)
                leaf_candidates = [record["leaf"] for record in result]

            # LLM 응답과 연계하여 노드 유사도 보정
            for leaf in leaf_candidates:
                leaf_similarity = calculate_similarity(text, leaf)
                if leaf_similarity >= similarity_threshold:
                    print(
                        f"최하위 노드 '{leaf}'는 유사도 {leaf_similarity:.2f}로 선택됨"
                    )
                    leaf_nodes.append(leaf)
                else:
                    print(
                        f"최하위 노드 '{leaf}'는 유사도 {leaf_similarity:.2f}로 선택되지 않음"
                    )

        # LLM 응답 기반 추가 탐색
        if not leaf_nodes:
            print("[INFO] LLM 응답을 기반으로 추가 탐색 시도")
            llm_suggestion = verify_classification_with_llm(subcategory, text)
            if llm_suggestion != "부적합":
                print(f"[INFO] LLM 제안된 카테고리: {llm_suggestion}")
                # 제안된 카테고리를 사용해 추가 검색 로직 구현
                leaf_nodes += find_leaf_nodes(
                    text, llm_suggestion, similarity_threshold
                )

    return leaf_nodes


def verify_classification_with_llm(classification, text):
    prompt = (
        f"다음 문제: {text} 가 분류 '{classification}'에 정확히 적합한지 평가해주세요. "
        "적합하지 않다면 '부적합'으로, 적합하다면 '적합'으로만 대답해주세요."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=50,
            temperature=0.5,
        )
        result = response.choices[0].message["content"].strip()
        print(f"LLM 응답: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] LLM 검증 실패: {e}")
        return "부적합"


def process_math_problem(problem):
    # 1단계: 키워드 및 대분류 추출
    raw_category = extract_category_from_math_problem(problem)
    print(f"추출된 대분류 (원본): {raw_category}")

    # 2단계: 하위 노드 탐색
    leaf_nodes = find_leaf_nodes(problem, raw_category, similarity_threshold=0.5)
    if not leaf_nodes:
        print("하위 노드를 찾을 수 없습니다. 프로세스를 종료합니다.")
        return

    print(f"찾은 하위 노드: {leaf_nodes}")

    # 3단계: 최종 검증
    verified_labels = []
    for leaf in leaf_nodes:
        verification = verify_classification_with_llm(leaf, problem)
        if verification == "적합":
            verified_labels.append(leaf)

    if verified_labels:
        print(f"최종 라벨: {verified_labels}")
    else:
        print("적합한 라벨을 찾을 수 없습니다.")


# .env 파일 로드
load_dotenv()

# 환경 변수 불러오기
openai_api_key = os.getenv("OPENAI_API_KEY")
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
INDEX_NAME = "index_name"

# Neo4j 데이터베이스 연결
print("[INFO] Neo4j 드라이버 초기화 중...")
driver = GraphDatabase.driver(uri, auth=(username, password))
try:
    with driver.session() as session:
        print("[INFO] Neo4j 연결 성공.")
except Exception as e:
    print(f"[ERROR] Neo4j 연결 실패: {e}")
    exit(1)


# Custom OpenAI Embeddings
class CustomOpenAIEmbeddings:
    def __init__(self, api_key, model="text-embedding-ada-002"):
        openai.api_key = api_key
        self.model = model

    def embed_query(self, query):
        print(f"[INFO] OpenAI Embedding 생성 요청: {query}")
        try:
            response = openai.Embedding.create(model=self.model, input=query)
            embedding = response["data"][0]["embedding"]
            print("[INFO] Embedding 생성 성공.")
            return embedding
        except Exception as e:
            print(f"[ERROR] Embedding 생성 실패: {e}")
            raise


# Custom Embeddings 객체 생성
embedder = CustomOpenAIEmbeddings(api_key=openai_api_key)


# VectorRetriever 클래스 정의
class VectorRetriever:
    def __init__(self, driver, index_name, embedder):
        self.driver = driver
        self.index_name = index_name
        self.embedder = embedder

    def retrieve(self, query_text, category, top_k=5):
        print(f"[INFO] Query Embedding 생성 중: {query_text}")
        query_embedding = self.embedder.embed_query(query_text)

        cypher_query = """
            MATCH (c:Category {name: $category})-[:HAS_CHILD]->(n:Subcategory)
            WHERE n.vector IS NOT NULL
            WITH n, n.vector AS node_vector, $query_vector AS query_vector
            WITH n,
                reduce(s = 0.0, i IN range(0, size(node_vector)-1) | s + node_vector[i] * query_vector[i]) AS dot_product,
                reduce(s = 0.0, i IN range(0, size(node_vector)-1) | s + node_vector[i]^2) AS node_magnitude,
                reduce(s = 0.0, i IN range(0, size(query_vector)-1) | s + query_vector[i]^2) AS query_magnitude
            WITH n, dot_product / (sqrt(node_magnitude) * sqrt(query_magnitude)) AS similarity
            WHERE similarity IS NOT NULL AND similarity >= 0.5
            RETURN n.name AS node_name, similarity
            ORDER BY similarity DESC
            LIMIT $top_k
        """

        print("[INFO] Cypher 쿼리 실행 중...")
        results = []
        try:
            with self.driver.session() as session:
                result = session.run(
                    cypher_query,
                    query_vector=query_embedding,
                    category=category,
                    top_k=top_k,
                )
                results = [
                    {"node": record["node_name"], "score": record["similarity"]}
                    for record in result
                ]
                # 필터링 함수 호출
                results = filter_nodes_by_category(results, category)
                print(f"[INFO] 쿼리 결과 (Filtered): {results}")
        except Exception as e:
            print(f"[ERROR] Cypher 쿼리 실행 실패: {e}")
        return results


# Retriever 객체 생성
retriever = VectorRetriever(driver, INDEX_NAME, embedder)


# PromptTemplate 정의
prompt_template = PromptTemplate(
    input_variables=["context"],
    template="Please answer the question based on the context provided: {context}",
)

# OpenAI LLM 생성
llm = OpenAI(model="gpt-3.5-turbo")


class GraphRAG:
    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm

    def search(self, query_text, category, retriever_config):
        print("[INFO] GraphRAG 검색 시작.")
        try:
            results = self.retriever.retrieve(
                query_text=query_text, category=category, **retriever_config
            )
            print(f"[INFO] 검색된 유사 항목: {results}")

            # 검색 결과 기반으로 LLM 사용
            context = "\n".join(
                [f"- {r['node']} (유사도: {r['score']:.2f})" for r in results]
            )
            final_prompt = f"다음 문맥을 기반으로 질문에 답해주세요:\n\n{context}\n\n질문: {query_text}"
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": final_prompt},
                ],
                max_tokens=100,
            )
            llm_response = response.choices[0].message["content"].strip()
            print("[INFO] LLM 응답 생성 성공.")
            return {"answer": results, "llm_response": llm_response}
        except Exception as e:
            print(f"[ERROR] GraphRAG 검색 실패: {e}")
            raise


rag = GraphRAG(retriever=retriever, llm=llm)

# 문제 처리 실행
problem = "아래 그림의 삼각형을 알맞게 분류하세요."
process_math_problem(problem)

# Neo4j 드라이버 종료
driver.close()
print("[INFO] Neo4j 드라이버 종료 완료")

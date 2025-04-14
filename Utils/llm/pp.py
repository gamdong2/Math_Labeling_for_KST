import openai
import os
import numpy as np
from dotenv import load_dotenv
from neo4j import GraphDatabase
import torch
from langchain_community.chat_models import ChatOllama
import json

# LLM을 사용한 수학 키워드 및 대분류 추출 함수
def extract_keywords_and_category_from_math_problem(text):
    prompt = (
        "다음 수학 문제에서 수학과 직접적으로 관련된 키워드와 가장 적합한 대분류를 추출하세요. "
        "키워드는 '키워드:'로 시작하고 대분류는 '대분류:'로 시작하여 각각 추출해주세요. "
        "대분류는 '변화와 관계', '도형과 측정', '자료와 가능성' 중에서 하나를 먼저 확인하고, "
        "그래프나 표와 관련된 문제는 우선적으로 '자료와 가능성'으로 분류하고, "
        "길이, 넓이, 들이, 무게 등의 단위 관련 문제는 '도형과 측정'으로 분류하며, "
        "배열, 규칙, 비율과 관련된 문제는 '변화와 관계'로 분류하세요. "
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
    return response.choices[0].message["content"].strip()


# 키워드 전처리 함수
def preprocess_keywords(raw_keywords):
    # 키워드 부분만 추출
    keywords = raw_keywords.split("키워드:")[1].strip().split(", ")
    # 각 키워드를 소문자로 변환하여 리스트로 반환
    return [kw.lower() for kw in keywords]

# 시드 고정
def set_seed(seed=12345):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# 시드 고정 설정
set_seed()

def calculate_similarity(keywords, leaf):
    """
    키워드와 리프 간의 유사도를 계산하는 함수 (GraphRAG)
    :param keywords: 키워드 리스트
    :param leaf: 리프 노드 이름
    :return: 유사도 값
    """
    query_keywords = " ".join(keywords)
    query_text = f"Calculate similarity between {query_keywords} and {leaf}"

    # GraphRAG를 통해 유사도 계산
    response = rag.search(query_text=query_text, retriever_config={"top_k": 1})
    similarity_score = response.answer[0].get("similarity", 0.0)

    return similarity_score

def find_similar_nodes_from_graph(keywords, category, level, similarity_threshold=0.8):
    """
    특정 카테고리 내에서 레벨별로 키워드와 유사도가 높은 항목을 탐색.
    :param keywords: 키워드 리스트
    :param category: 대분류/중분류 이름
    :param level: 검색할 노드의 레벨 ("Subcategory", "Leaf" 등)
    :param similarity_threshold: 유사도 임계값
    :return: 유사도가 높은 노드 리스트
    """
    # GraphRAG를 사용하여 유사도 검색
    query_text = f"Find nodes related to {', '.join(keywords)} in category {category} at level {level}"
    print(f"Query Text: {query_text}")

    try:
        response = rag.search(query_text=query_text, retriever_config={"top_k": 5})
        print(f"Response Type: {type(response)}")
        print(f"Raw Response: {response}")

        # JSON 파싱 시도
        if isinstance(response, str):
            response_data = json.loads(response)
        else:
            response_data = response  # JSON 객체라면 그대로 사용

        # 유사도 필터링
        if "answer" in response_data:
            matched_nodes = [
                node
                for node in response_data["answer"]
                if node.get("similarity", 0) >= similarity_threshold
            ]
            print(f"Matched Nodes: {matched_nodes}")
            return [node["name"] for node in matched_nodes]
        else:
            print("No 'answer' field in response data.")
            return []

    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []
    
def find_subcategories(keywords, category):
    """
    대분류(category)에서 가장 유사한 중분류 하나를 찾는다.
    :param keywords: 키워드 리스트
    :param category: 대분류 이름
    :return: 가장 유사한 중분류
    """
    best_match = find_similar_nodes_from_graph(keywords, category, level="Subcategory")
    if best_match:
        return best_match

    print(f"중분류를 찾을 수 없습니다. 대분류: {category}")
    return []

def find_leaf_nodes(keywords, category_name, similarity_threshold=0.8):
    # 중분류 찾기
    subcategories = find_subcategories(keywords, category_name)
    if not subcategories:
        print(f"중분류를 찾을 수 없습니다. 대분류: {category_name}")
        return []

    leaf_nodes = []
    for subcategory in subcategories:
        print(f"중분류 '{subcategory}'에서 하위 노드 탐색 시작")
        # 해당 중분류에 연결된 item 찾기
        items = find_similar_nodes_from_graph(
            keywords,
            subcategory,
            level="Item",
            similarity_threshold=similarity_threshold,
        )
        if not items:
            print(f"중분류 '{subcategory}'에 연결된 item이 없습니다.")
            continue
        print(f"중분류 '{subcategory}'에 연결된 item: {items}")

        for item in items:
            # 해당 item에 연결된 leaf 찾기
            query = """
            MATCH (i:Item {name: $item})-[:HAS_CHILD]->(ln:Leaf)
            RETURN ln.name AS leaf
            """
            # Neo4j 세션을 열어서 쿼리 실행
            with driver.session() as session:
                result = session.run(query, item=item)
                leaf_candidates = [record["leaf"] for record in result]

            for leaf in leaf_candidates:
                # 최하위 노드(leaf) 유사도 검증
                leaf_similarity = calculate_similarity(keywords, leaf)
                if leaf_similarity >= similarity_threshold:
                    print(
                        f"최하위 노드 '{leaf}'는 유사도 {leaf_similarity:.2f}로 선택됨"
                    )
                    leaf_nodes.append(leaf)
                else:
                    print(
                        f"최하위 노드 '{leaf}'는 유사도 {leaf_similarity:.2f}로 선택되지 않음"
                    )

    return leaf_nodes

def verify_classification_with_llm(classification, keywords):
    prompt = (
        f"다음 키워드: {', '.join(keywords)} 가 분류 '{classification}'에 정확히 적합한지 평가해주세요. "
        f"해당 분류가 모든 {', '.join(keywords)} 와 직접적으로 연관되어야 합니다. 예를 들어, 다음과 같은 경우를 고려하세요:"
        "키워드 '덧셈'이 분류 '곱셈'에 해당하는 경우 '부적합'으로 응답해야 하며, "
        "키워드 '원뿔'이 분류 '직육면체'에 해당하는 경우 '부적합'으로 응답해야 합니다. "
        "적합하지 않다면 '부적합'으로, 적합하다면 '적합'으로만 대답해주세요. "
    )
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
    print(f"LLM 응답: {result}")  # 응답 메시지 출력 (디버깅용)
    return result

def process_math_problem(problem):
    # 1단계: 키워드 및 대분류 추출
    raw_keywords_and_category = extract_keywords_and_category_from_math_problem(problem)
    print(f"추출된 키워드 및 대분류 (원본): {raw_keywords_and_category}")

    # 키워드와 대분류 분리
    try:
        raw_keywords, most_similar_category = raw_keywords_and_category.split(
            "\n대분류: "
        )
    except ValueError:
        print("응답 형식이 맞지 않습니다. 기본값으로 '수와 연산'을 사용합니다.")
        raw_keywords = raw_keywords_and_category
        most_similar_category = "수와 연산"

    keywords = preprocess_keywords(raw_keywords)
    print(f"전처리된 키워드: {keywords}")
    print(f"가장 유사한 대분류: {most_similar_category}")

    # 2단계: 하위 노드 탐색
    leaf_nodes = find_leaf_nodes(
        keywords, most_similar_category, similarity_threshold=0.6
    )
    if not leaf_nodes:
        print("하위 노드를 찾을 수 없습니다. 프로세스를 종료합니다.")
        return

    print(f"찾은 하위 노드: {leaf_nodes}")

    # 3단계: 최종 검증
    verified_labels = []
    for leaf in leaf_nodes:
        verification = verify_classification_with_llm(leaf, keywords)
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


# Custom OpenAI Embeddings
class CustomOpenAIEmbeddings:
    def __init__(self, api_key, model="text-embedding-ada-002"):
        openai.api_key = api_key
        self.model = model

    def embed_query(self, query):
        print(f"[INFO] OpenAI Embedding 생성 요청: {query}")
        try:
            response = openai.Embedding.create(
                model=self.model,
                input=query,
            )
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

    def retrieve(self, query_text, top_k=5):
        print(f"[INFO] Query Embedding 생성 중: {query_text}")
        query_embedding = self.embedder.embed_query(query_text)  # Embedding 생성

        cypher_query = """
        MATCH (n:VectorNode)
        WHERE n.vector IS NOT NULL
        WITH n, n.vector AS node_vector, $query_vector AS query_vector
        WITH n, 
            reduce(s = 0.0, i IN range(0, size(node_vector)-1) | 
                s + node_vector[i] * query_vector[i]) AS dot_product, 
            reduce(s = 0.0, i IN range(0, size(node_vector)-1) | 
                s + node_vector[i]^2) AS node_magnitude, 
            reduce(s = 0.0, i IN range(0, size(query_vector)-1) | 
                s + query_vector[i]^2) AS query_magnitude
        WITH n, dot_product / (sqrt(node_magnitude) * sqrt(query_magnitude)) AS similarity
        WHERE similarity >= 0.5
        RETURN n.name AS node_name, similarity
        ORDER BY similarity DESC
        LIMIT $top_k
        """
        print("[INFO] Cypher 쿼리 실행 중...")

        results = []
        try:
            with self.driver.session() as session:
                # query_vector를 파라미터로 전달
                result = session.run(
                    cypher_query, query_vector=query_embedding, top_k=top_k
                )
                results = [
                    {"node": record["node_name"], "score": record["similarity"]}
                    for record in result
                ]
                print(f"[INFO] 쿼리 결과: {results}")
        except Exception as e:
            print(f"[ERROR] Cypher 쿼리 실행 실패: {e}")
        return results


class GraphRAG:
    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm

    def search(self, query_text, retriever_config):
        print("[INFO] GraphRAG 검색 시작.")
        try:
            results = self.retriever.retrieve(query_text, **retriever_config)
            print(f"[INFO] 검색된 유사 항목: {results}")
            context = "\n".join([str(r["node"]) for r in results])
            # predict() 메서드에 'text' 인자 전달 수정
            llm_response = self.llm.predict(
                context=context, input_text=query_text, text=context
            )
            print("[INFO] LLM 응답 생성 성공.")
            return llm_response
        except Exception as e:
            print(f"[ERROR] GraphRAG 검색 실패: {e}")
            raise


# Retriever 객체 생성
retriever = VectorRetriever(driver, INDEX_NAME, embedder)

# LangChain LLM (예시로 ChatOllama 사용)
llm = ChatOllama(model="llama3:8b")

# GraphRAG 객체 생성
rag = GraphRAG(retriever=retriever, llm=llm)


# 문제 처리 실행
problem = "기차에 사람이 $1500$ 명 타고 있었습니다. 이번 역에서 $80$ 명이 내리고 $124$ 명이 탔습니다. 지금 기차 안에 있는 사람은 모두 몇 명인지 구해 보세요."
process_math_problem(problem)

# Neo4j 드라이버 종료
driver.close()
print("[INFO] Neo4j 드라이버 종료 완료")
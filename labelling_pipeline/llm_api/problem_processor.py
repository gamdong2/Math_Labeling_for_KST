import time
from openai_utils import (
    extract_math_concepts,
    determine_major_category,
    extract_leaf_category_within_major_category,
)


def process_math_problem(problem_text, category_map, figure_text=None, model="gpt-4"):
    """
    문제를 분석하여 대분류 및 최하위 분류를 추출합니다.
    figure_text가 주어지면 해당 텍스트도 함께 고려하여 분석합니다.

    Parameters:
    - problem_text (str): 수학 문제 텍스트
    - category_map (dict): 대분류와 로컬 JSON 데이터 매핑
    - figure_text (str, optional): 문제와 관련된 그림 설명 텍스트
    - model (str): GPT 모델 이름 (기본값: "gpt-4")

    Returns:
    - tuple: (대분류, 최하위 분류, 대분류 추출 시간, 최하위 분류 추출 시간)
    """
    # Step 1: 문제 분석을 통해 주요 개념 및 대분류 추출
    start_time = time.time()

    # 문제 텍스트와 figure_text를 합쳐서 분석
    combined_text = problem_text
    if figure_text:
        combined_text += "\n" + figure_text

    # 수학적 개념 추출
    math_concept = extract_math_concepts(combined_text)
    major_category = determine_major_category(math_concept)
    category_time = time.time() - start_time
    print(f"[INFO] 추출된 대분류: {major_category}")

    # Step 2: 로컬 JSON 데이터를 검색하여 최하위 분류 정보 추출
    leaf_category_data = None
    leaf_time = 0  # 최하위 분류 추출에 걸린 시간

    if major_category:
        try:
            # 로드맵 데이터에서 대분류에 해당하는 데이터 가져오기
            start_leaf_time = time.time()
            json_data = category_map.get(major_category)

            if json_data:
                # 최하위 분류 추출
                leaf_category_data = extract_leaf_category_within_major_category(
                    math_concept, major_category, json_data
                )
                leaf_time = time.time() - start_leaf_time

                if leaf_category_data:
                    print(f"[INFO] 최하위 분류: {leaf_category_data}")
                else:
                    print(
                        f"[ERROR] '{major_category}' 대분류 내 최하위 분류 데이터를 찾을 수 없습니다."
                    )
            else:
                print(
                    f"[ERROR] '{major_category}' 대분류에 해당하는 로드맵 데이터를 찾을 수 없습니다."
                )
        except Exception as e:
            print(f"[ERROR] 최하위 분류 추출 중 오류 발생: {e}")

    # Step 3: 결과 반환
    return major_category, leaf_category_data, category_time, leaf_time

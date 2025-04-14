import openai
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv(dotenv_path="../pipeline/.env", override=True)

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")


def extract_math_concepts(problem_text):
    """
    문제에서 수학적 개념을 추출합니다.
    """
    prompt = (
        "다음은 한국 초등학교 수학 문제입니다:\n"
        f"{problem_text}\n\n"
        "문제를 분석하여 해결하는 데 필요할 것으로 예상되는 주요 초등 수학적 개념을 추출하세요.\n"
        "길이, 들이, 넓이, 무게, 부피 등의 단위나 도형 및 선분, 직선, 규칙이나 배열, 표나 그래프가 문제에 나오는 경우 해당 개념은 반드시 추출하는 개념에 포함하세요.\n"
        "추출된 주요 개념의 명칭만 작성하세요."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.5,
        )
        math_concept = response.choices[0].message["content"].strip()
        print(f"[INFO] 추출된 수학적 개념: {math_concept}")
        return math_concept
    except Exception as e:
        print(f"[ERROR] 수학적 개념 추출 실패: {e}")
        return None


def determine_major_category(math_concept):
    """
    수학적 개념을 분석하여 적합한 대분류를 결정합니다.
    """
    prompt = (
        f"다음은 추출된 수학적 개념입니다:\n{math_concept}\n\n"
        "이 개념과 가장 유사한 대분류를 '수와 연산', '변화와 관계', '도형과 측정', '자료와 가능성' 중에서 선택하세요. "
        "단, 다음 규칙을 따라 우선적으로 선택하세요:\n"
        "- 그래프나 표와 관련된 문제는 '자료와 가능성'\n"
        "- 길이, 넓이, 들이, 무게 등의 단위, 도형, 각도, 선분 및 직선은 '도형과 측정'\n"
        "- 비례, 대응, 비교, 배열, 규칙은 '변화와 관계'\n"
        "- 사칙연산(덧셈, 뺄셈, 곱셈, 나눗셈)은 '수와 연산'\n"
        "어디에도 속하지 않는 경우 '수와 연산'으로 분류하세요."
        "대분류명만 문장 부호를 제외하고 작성하세요."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.5,
        )
        major_category = response.choices[0].message["content"].strip()
        print(f"[INFO] 결정된 대분류: {major_category}")
        return major_category
    except Exception as e:
        print(f"[ERROR] 대분류 결정 실패: {e}")
        return None


def extract_leaf_category_within_major_category(
    math_concept, major_category, json_summary
):
    """
    JSON 데이터 요약을 기반으로, 특정 대분류 내에서 최하위 분류를 추출합니다.
    """
    prompt = (
        f"다음은 추출된 수학적 개념입니다:\n{math_concept}\n\n"
        f"대분류: {major_category}\n\n"
        "다음은 학습 주제의 계층 구조입니다. 이 계층 구조에서 해당 대분류에 속하는 내용만 사용하여 최하위 분류를 추출하세요:\n"
        f"{json_summary}\n\n"
        "추출된 개념에 가장 유사한 최하위 분류(학습 주제)를 계층 구조에서 추출하세요. "
        "단, 자식이 없는 최하위 분류만 추출하며, 가능한 한 1개만 추출하세요. "
        "최하위 분류가 불가피하게 여러 개 필요한 경우 최대 2개까지만 콤마로 구분하여 추출하세요.\n\n"
        "최하위 분류명만 문장 부호를 제외하고 작성하세요."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.5,
        )
        leaf_category = response.choices[0].message["content"].strip()
        print(f"[INFO] 대분류 '{major_category}' 내 최하위 분류: {leaf_category}")
        return leaf_category
    except Exception as e:
        print(f"[ERROR] 최하위 분류 추출 실패: {e}")
        return None

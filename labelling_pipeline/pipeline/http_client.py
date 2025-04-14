import httpx
import logging
from typing import Dict, Any

# 각 API의 엔드포인트 URL 설정
# YOLO_API_URL = "http://yolo_api:8000/extract_bboxes"
OCR_API_URL = "http://ocr_api:8001/extract_text"
LLM_API_URL = "http://llm_api:8002/process_problem"

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# async def call_yolo_api(image_path: str) -> Dict[str, Any]:
#     """YOLO API에 이미지 경로를 보내고, 객체 인식 결과를 반환"""
#     try:
#         async with httpx.AsyncClient() as client:
#             with open(image_path, "rb") as image_file:
#                 response = await client.post(YOLO_API_URL, files={"image": image_file})

#         response.raise_for_status()  # HTTP 상태 코드가 200번대가 아니면 예외 발생
#         return response.json()  # JSON 형식으로 응답 받기
#     except httpx.RequestError as e:
#         logger.error(f"YOLO API 호출 실패: {e}")
#         return {"error": str(e)}


async def call_ocr_api(image_path: str) -> Dict[str, Any]:
    """OCR API에 이미지를 보내고 텍스트를 반환"""
    try:
        async with httpx.AsyncClient() as client:
            with open(image_path, "rb") as image_file:
                response = await client.post(OCR_API_URL, files={"image": image_file})

        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"OCR API 호출 실패: {e}")
        return {"error": str(e)}


async def call_llm_api(question_text: str) -> Dict[str, Any]:
    """LLM API에 질문 텍스트를 보내고, 카테고리와 라벨을 반환"""
    try:
        async with httpx.AsyncClient() as client:
            payload = {"question_text": question_text}
            response = await client.post(LLM_API_URL, json=payload)

        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"LLM API 호출 실패: {e}")
        return {"error": str(e)}

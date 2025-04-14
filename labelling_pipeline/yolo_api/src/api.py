# src/api.py
from typing import List
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
import asyncio
import os
from contextlib import asynccontextmanager
from config import (
    S3_BUCKET_NAME,
    YOLO_MODEL_PATH,
    LOCAL_YOLO_MODEL_PATH,
    CROPPED_IMAGES_DIR,
    DOWNLOADS_DIR,
)
from s3_utils import create_s3_client
from ocr_utils import save_cropped_image_path
from yolo_model import (
    download_image_from_s3,
    process_image_with_craft,
    process_image_with_yolo_and_craft,
    convert_numpy_to_python,
    flatten,
    save_coordinates,
    save_failed_boxes,
)
from model_manager import model_manager  # 추가
from webhook_handler import router as webhook_router  # 추가
import logging
from fastapi.security.api_key import APIKeyHeader
from fastapi import Security

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YOLO+CRAFT Image Processing API")

# Webhook 핸들러 라우터 포함
app.include_router(webhook_router, prefix="/api")

class CoordinatesResponse(BaseModel):
    message: str
    coordinates: List[List[int]]
    cropped_image_paths: List[str]

class ModelUpdateRequest(BaseModel):
    s3_key: str  # S3에 저장된 새로운 모델의 키

# API 키 인증 설정
API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "access_token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    else:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("서버 시작 중...")

    try:
        # 모델 초기화는 model_manager에서 처리됨
        yield

    except Exception as e:
        logger.error(f"Error during model download or load: {e}")

    finally:
        logger.info("서버 종료 중...")

app = FastAPI(lifespan=lifespan, title="YOLO+CRAFT Image Processing API")

@app.get("/", summary="API 상태 확인")
async def root():
    return {"message": "FastAPI 서버가 실행 중입니다!"}

@app.post("/extract_bboxes/", response_model=CoordinatesResponse, summary="이미지에서 바운딩 박스 추출 및 저장")
async def extract_bboxes_from_image(
    image_path: str = Query(..., title="S3 Image Path", description="S3에 저장된 이미지의 경로"),
):
    """
    이미지의 S3 경로를 받아 이미지를 다운로드하고, YOLO 모델을 사용하여 바운딩 박스를 추출합니다.
    크롭된 이미지를 저장하고, 해당 경로를 반환합니다.
    """
    try:
        # S3에서 이미지 다운로드
        local_image_path = os.path.join(DOWNLOADS_DIR, os.path.basename(image_path))
        os.makedirs(os.path.dirname(local_image_path), exist_ok=True)
        image = download_image_from_s3(S3_BUCKET_NAME, image_path, local_image_path)
        if image is None:
            raise HTTPException(status_code=400, detail="S3에서 이미지 로드 실패")

        image_name = os.path.splitext(os.path.basename(image_path))[0]

        # CRAFT 또는 YOLO+CRAFT 결과 얻기
        craft_result = process_image_with_craft(local_image_path)
        coordinates = []
        cropped_image_paths = []

        if craft_result is not None and len(craft_result["boxes"]) > 0:
            # CRAFT로 텍스트 영역 감지
            coordinates = [
                convert_numpy_to_python(np.array(box).astype(int))
                for box in craft_result["boxes"]
                if box is not None and len(box) > 0
            ]
            save_coordinates(coordinates, "coordinates.txt")
            # CRAFT 사용 시 크롭된 이미지를 저장하지 않음 (필요 시 추가 가능)
        else:
            # YOLO+CRAFT로 텍스트 영역 감지 및 크롭
            all_text_boxes, failed_boxes, cropped_image_paths = process_image_with_yolo_and_craft(
                yolo_model=model_manager.yolo_model,  # model_manager에서 yolo_model 사용
                image=image,
                image_name=image_name
            )
            coordinates = [convert_numpy_to_python(coord) for coord in all_text_boxes]
            coordinates = flatten(coordinates)
            save_coordinates(coordinates, "coordinates.txt")
            if failed_boxes:
                save_failed_boxes(failed_boxes, "failed_boxes.txt")

            # 크롭된 이미지를 저장 (OCR API는 별도로 처리)
            # 현재는 cropped_image_paths에 경로만 저장

        # OCR API는 별도의 서비스에서 처리하므로, 경로만 반환
        return CoordinatesResponse(
            message="텍스트 감지 완료",
            coordinates=coordinates,
            cropped_image_paths=cropped_image_paths,
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"API 처리 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_model/", summary="YOLO 모델 업데이트")
async def update_model(request: ModelUpdateRequest, api_key: str = Depends(get_api_key)):
    """
    새로운 모델을 S3에서 다운로드하여 현재 서빙 중인 모델을 교체합니다.
    """
    try:
        new_model_s3_key = request.s3_key
        model_manager.update_model(new_model_s3_key)
        return {"message": "모델 업데이트 성공", "new_model_path": model_manager.current_model_path}
    except Exception as e:
        logger.error(f"모델 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail="모델 업데이트 실패")

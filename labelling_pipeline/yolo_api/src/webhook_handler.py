# src/webhook_handler.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from model_manager import model_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ModelUpdateEvent(BaseModel):
    model_name: str
    version: int
    status: str
    source: str  # S3 키 또는 모델 경로

@router.post("/webhook/model_update/", summary="MLflow 모델 업데이트 Webhook")
async def handle_model_update(event: ModelUpdateEvent):
    """
    MLflow 모델 레지스트리에서 모델 업데이트 이벤트를 수신합니다.
    """
    try:
        if event.status.lower() == "ready":
            # 새로운 모델 버전이 준비되었을 때
            new_model_s3_key = event.source  # S3 키 또는 모델 경로
            model_manager.update_model(new_model_s3_key)
            return {"message": "모델 업데이트 성공"}
        else:
            logger.info(f"모델 업데이트 이벤트 상태: {event.status}")
            return {"message": f"모델 상태: {event.status}"}
    except Exception as e:
        logger.error(f"모델 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail="모델 업데이트 실패")

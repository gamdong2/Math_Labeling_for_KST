# src/model_manager.py
import os
import logging
from yolo_model import initialize_models
from s3_utils import create_s3_client
from config import S3_BUCKET_NAME, YOLO_MODEL_PATH, LOCAL_YOLO_MODEL_PATH, CROPPED_IMAGES_DIR
import shutil
import time

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self.s3_client = create_s3_client()
        self.current_model_path = LOCAL_YOLO_MODEL_PATH
        self.initialize_current_model()

    def initialize_current_model(self):
        """현재 모델을 초기화합니다."""
        if os.path.exists(self.current_model_path):
            initialize_models(self.current_model_path)
            logger.info(f"현재 모델 초기화 완료: {self.current_model_path}")
        else:
            logger.error(f"현재 모델 파일이 존재하지 않습니다: {self.current_model_path}")
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {self.current_model_path}")

    def download_latest_model(self, s3_key, local_path):
        """S3에서 최신 모델을 다운로드합니다."""
        try:
            with open(local_path, "wb") as f:
                self.s3_client.download_fileobj(S3_BUCKET_NAME, s3_key, f)
            logger.info(f"최신 모델 다운로드 완료: {s3_key} to {local_path}")
        except Exception as e:
            logger.error(f"모델 다운로드 실패: {e}")
            raise

    def update_model(self, new_model_s3_key, retries=3, delay=5):
            """새로운 모델로 교체합니다. 리트라이 로직 포함."""
            temp_model_path = self.current_model_path + ".tmp"
            attempt = 0
            while attempt < retries:
                try:
                    # S3에서 새로운 모델 다운로드
                    self.download_latest_model(new_model_s3_key, temp_model_path)

                    # 새로운 모델을 로드
                    initialize_models(temp_model_path)

                    # 기존 모델을 백업하고, 새 모델로 교체
                    backup_path = self.current_model_path + ".bak"
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    os.rename(self.current_model_path, backup_path)
                    os.rename(temp_model_path, self.current_model_path)
                    logger.info(f"모델 교체 완료: {self.current_model_path}")

                    # 현재 모델의 S3 키 업데이트
                    self.current_model_s3_key = new_model_s3_key

                    return
                except Exception as e:
                    logger.error(f"모델 교체 시도 {attempt + 1}/{retries} 실패: {e}")
                    attempt += 1
                    time.sleep(delay)

            logger.error("모델 교체가 모두 실패했습니다.")
            raise Exception("모델 교체 실패")

    def rollback_model(self):
        """백업된 모델로 롤백합니다."""
        backup_path = self.current_model_path + ".bak"
        if os.path.exists(backup_path):
            os.rename(self.current_model_path, self.current_model_path + ".tmp")
            os.rename(backup_path, self.current_model_path)
            initialize_models(self.current_model_path)
            logger.info(f"모델 롤백 완료: {self.current_model_path}")
        else:
            logger.error("백업된 모델이 존재하지 않습니다.")
            raise FileNotFoundError("백업된 모델이 없습니다.")

# 전역 인스턴스
model_manager = ModelManager()
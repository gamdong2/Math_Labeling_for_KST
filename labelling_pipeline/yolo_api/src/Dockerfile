# Python 3.9 기반 이미지
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /labelling_pipeline/yolo_api


# 필요한 시스템 라이브러리 설치 (예: OpenCV, PyTorch 등)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src
COPY models/ ./models

# # YOLO 모델을 로드하는 코드 및 FastAPI 애플리케이션 복사
# COPY yolo_api.py .
# COPY yolo_model.py .

# 다운로드 및 크롭된 이미지 디렉토리 생성
RUN mkdir -p downloads cropped_images

# 환경 변수 설정
ENV PYTHONPATH=/labelling_pipeline/yolo_api/src

# 서버 실행 명령어
CMD ["uvicorn", "yolo_api:app", "--host", "0.0.0.0", "--port", "8000"]

# Python 3.9 기반 이미지
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /labelling_pipeline/ocr_api

# 환경 변수 설정
ENV PYTHONPATH=/labelling_pipeline

# 필요한 시스템 라이브러리 설치 (예: Tesseract, pytesseract 등)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# OCR 모델을 로드하는 코드 및 FastAPI 애플리케이션 복사
COPY ocr_api.py .
COPY ocr_model.py .

# yolo_api 폴더 복사
COPY ../yolo_api /labelling_pipeline/yolo_api

# 서버 실행 명령어
CMD ["uvicorn", "ocr_api:app", "--host", "0.0.0.0", "--port", "8001"]

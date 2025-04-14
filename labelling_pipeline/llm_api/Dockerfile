# Python 3.9 기반 이미지
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /labelling_pipeline/llm_api

# Python dependencies 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# LLM 모델 로드하는 코드 및 FastAPI 애플리케이션 복사
COPY json_utils.py .
COPY openai_utils.py .
COPY problem_processor.py .
COPY s3_utils.py .
COPY llm_api.py .
COPY llm_main.py .

# 서버 실행 명령어
CMD ["uvicorn", "llm_api:app", "--host", "0.0.0.0", "--port", "8002"]
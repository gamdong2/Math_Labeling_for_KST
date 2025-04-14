# Python 3.9 버전 이미지를 기반으로 설정
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /labelling_pipeline/pipline

# 필요한 패키지 설치
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스 코드 복사
COPY http_client.py .
COPY main.py .


# FastAPI 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

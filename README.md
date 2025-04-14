# 초등 영어 발음 채점 서비스
<p align="center">
  <img src=![Image](https://github.com/user-attachments/assets/164f3dff-54f0-45bf-9044-65054cb1c893) width="80%" alt="epa"/>
</p>

## Skills
<img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white"/>&nbsp;
<img src="https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white"/>&nbsp;
<img src="https://img.shields.io/badge/AWS_EC2-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white"/>&nbsp;
<img src="https://img.shields.io/badge/Airflow-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white"/>&nbsp;
<img src="https://img.shields.io/badge/MLflow-123F8C?style=for-the-badge&logo=mlflow&logoColor=white"/>&nbsp;
<img src="https://img.shields.io/badge/GPT--4_Turbo-9B59B6?style=for-the-badge&logo=openai&logoColor=white"/>&nbsp;
<img src="https://img.shields.io/badge/YOLO/CRAFT/OCR-FF5252?style=for-the-badge&logo=python&logoColor=white"/>&nbsp;
<img src="https://img.shields.io/badge/Github_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white"/>&nbsp;

## 프로젝트 상세
- **진행 기간** : 2024년 12월 2일 ~ 2025년 1월 12일 (총 42일)
- **프로젝트 유형** : 팀 프로젝트 (총 3명)

## 프로젝트 목표
- 초등 수학 문제 데이터를 KST 기반 학습 진단 시스템과 연동 가능한 형태로 자동 라벨링
- 텍스트 및 이미지 형태의 문제 모두 처리 가능한 파이프라인 설계
- 자동화된 학습 파이프라인을 구축하여 지속적인 모델 개선 지원

## 나의 역할 [팀원]
### OCR 모델 학습 파이프라인 구현
- OCR 학습 데이터 구성: 한국 소설 텍스트 기반 무문맥 문장 300만개 생성
- TRDG 라이브러리를 활용하여 OCR 학습용 이미지 데이터 생성
- Airflow DAG + MLflow 기반 자동 학습 및 버전 관리
- Lambda를 활용한 주기/조건 기반 자동 트리거 구성

### 라벨링 파이프라인 자동화
- YOLO/CRAFT로 이미지 내 텍스트 영역 검출 → OCR → GPT-4 Turbo로 라벨링
- 라벨링 결과를 PostgreSQL에 저장하고, API로 사용자에 제공

### CI/CD
- **CI**: GitHub Actions로 Docker 이미지 자동 생성 및 ECR에 푸시
- **CD**: Airflow DAG 실행 → 최신 Docker 이미지 Pull → 학습 및 배포 자동화

## 사용한 데이터 셋
- 교육과정 성취수준표 기반 수학 문항
- 공유마당 한국 소설 텍스트(14권) → 300만 개의 무문맥 학습 문장

## 문제 해결 사례
### OCR 모델 과적합 발생
- 초등 수학 문제만 학습한 TrOCR 모델이 실제 입력과 관계없이 특정 문장을 반복 출력
- → 한국 소설 텍스트를 학습 데이터로 추가하여 모델 일반화 성능 확보

### OCR 모델의 문맥 의존도
- 문맥에 의존하여 임의로 문장을 완성하려는 경향 발생
- → 무문맥 데이터로 전체 학습 데이터의 50% 구성하여 모델의 문맥 의존도 완화

## 프로젝트 결과
### 구현 기능
- 텍스트/이미지 문제 자동 분류 및 라벨링 처리 파이프라인 설계
- OCR 모델 학습 자동화 및 버전 관리 파이프라인 구축
- 학습된 모델을 기반으로 DB 저장 및 API 제공
- KST 기반 시스템과 연동 가능한 지식 구조 기반 라벨링 결과 생성

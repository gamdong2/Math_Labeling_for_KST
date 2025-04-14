# import random
# import boto3
# import json
# import os
# from json_utils import summarize_json_hierarchy


# # S3에서 JSON 파일을 로드하여 파싱
# def load_json_from_s3(bucket_name, file_path):
#     s3 = boto3.client("s3")
#     try:
#         # S3에서 파일을 읽어오기
#         response = s3.get_object(Bucket=bucket_name, Key=file_path)
#         content = response["Body"].read().decode("utf-8")

#         # 파일 내용이 비어 있지 않은지 확인
#         if not content.strip():  # 비어 있으면
#             print(f"[WARNING] 파일 '{file_path}'이 비어 있습니다.")
#             return None

#         return json.loads(content)  # JSON 파싱
#     except json.JSONDecodeError as e:
#         print(f"[ERROR] JSON 파싱 오류: {file_path} - {e}")
#         return None
#     except Exception as e:
#         print(f"[ERROR] S3에서 파일 로드 실패: {e}")
#         return None


# # S3에서 대분류와 일치하는 JSON 데이터를 검색
# def search_s3_files_for_category(bucket_name, prefix, target_category):
#     s3 = boto3.client("s3")
#     try:
#         # S3에서 객체 목록을 가져옴
#         result = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
#         for obj in result.get("Contents", []):
#             file_path = obj["Key"]

#             # 폴더인지 파일인지 확인
#             if file_path.endswith("/"):  # 폴더일 경우 건너뜀
#                 print(f"[INFO] '{file_path}'는 폴더입니다. 건너뜁니다.")
#                 continue

#             # JSON 파일 로드
#             json_data = load_json_from_s3(bucket_name, file_path)
#             if json_data:
#                 summary = summarize_json_hierarchy(json_data)
#                 if target_category in summary:
#                     return json_data

#         print(
#             f"[ERROR] S3 내 파일에서 대분류 '{target_category}'에 해당하는 데이터를 찾을 수 없습니다."
#         )
#     except Exception as e:
#         print(f"[ERROR] S3 파일 검색 중 오류 발생: {e}")
#     return None

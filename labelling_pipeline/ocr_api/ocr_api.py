import os
import shutil
import json
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
from ocr_model import load_ocr_model, perform_ocr_on_cropped_images

# from yolo_api.src.config import CROPPED_IMAGES_DIR  # 크롭된 이미지 폴더 경로

app = FastAPI()

# OCR 모델 관련 설정
LOCAL_MODEL_PATH = "C:/Users/boar2/Desktop/final_project/github/labelling_pipeline/ocr_api/models/final_model_1"

# 결과 저장 디렉토리
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# 1) 로컬 디렉터리에서 OCR 모델 로드
ocr_model, ocr_tokenizer, ocr_processor = load_ocr_model(LOCAL_MODEL_PATH)
if not ocr_model or not ocr_tokenizer or not ocr_processor:
    raise RuntimeError(
        f"[ERROR] OCR 모델 로드에 실패했습니다. 경로를 확인하세요: {LOCAL_MODEL_PATH}"
    )

CROPPED_IMAGES_DIR = "C:/Users/boar2/Desktop/final_project/github/labelling_pipeline/ocr_api/test_img"


@app.post("/extract_text/")
async def extract_text_from_folders():
    """
    여러 자식 폴더를 포함한 크롭된 이미지를 OCR 처리하고 결과를 반환
    """
    try:
        # 자식 폴더 확인
        if not os.path.exists(CROPPED_IMAGES_DIR):
            return JSONResponse(
                content={
                    "error": f"Cropped images directory not found: {CROPPED_IMAGES_DIR}"
                },
                status_code=400,
            )

        # 자식 폴더 리스트
        subfolders = [
            os.path.join(CROPPED_IMAGES_DIR, folder)
            for folder in os.listdir(CROPPED_IMAGES_DIR)
            if os.path.isdir(os.path.join(CROPPED_IMAGES_DIR, folder))
        ]
        if not subfolders:
            return JSONResponse(
                content={
                    "error": "No subfolders found in the cropped images directory."
                },
                status_code=400,
            )

        # 결과 저장
        folder_results = {}

        for subfolder in sorted(subfolders):
            print(f"[INFO] Processing folder: {subfolder}")

            # 이미지 파일 리스트 (오름차순 정렬)
            image_paths = [
                os.path.join(subfolder, fname)
                for fname in sorted(os.listdir(subfolder))
                if fname.lower().endswith((".png", ".jpg", ".jpeg"))
            ]

            if not image_paths:
                print(f"[WARN] No images found in {subfolder}. Skipping...")
                continue

            # OCR 수행
            folder_texts = perform_ocr_on_cropped_images(
                image_paths=image_paths,
                model=ocr_model,
                tokenizer=ocr_tokenizer,
                image_processor=ocr_processor,
                image_size=384,
            )

            # 폴더 이름을 키로 결과 저장
            folder_name = os.path.basename(subfolder)
            folder_results[folder_name] = " ".join(folder_texts).strip()

        # 최종 결과 JSON 생성 및 저장
        result = {
            "cropped_images_dir": CROPPED_IMAGES_DIR,
            "ocr_results": folder_results,
        }
        output_json_path = os.path.join(RESULTS_DIR, "ocr_results.json")
        with open(output_json_path, "w", encoding="utf-8") as json_file:
            json.dump(result, json_file, ensure_ascii=False, indent=4)

        print(f"[INFO] OCR results saved to: {output_json_path}")

        return JSONResponse(
            content={
                "message": "OCR processing complete.",
                "result_file": output_json_path,
            }
        )

    except Exception as e:
        print(f"[ERROR] Failed to process images: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

    # 임시 디렉토리 정리: 처리 후 크롭된 이미지 모두 삭제  # <- 이미지 사라지니까 테스트 불편해서 잠시 가리기
    # finally:
    # if os.path.exists(CROPPED_IMAGES_DIR):
    # shutil.rmtree(CROPPED_IMAGES_DIR)
    # print(f"[INFO] Temporary directory {CROPPED_IMAGES_DIR} has been cleaned up.")


# -------------------------------------------------------------------------
# 추가: 단순 파이썬 스크립트 실행 시 동작할 로직   ＜－ 테스트 이후 삭제
# -------------------------------------------------------------------------
if __name__ == "__main__":
    """
    'python ocr_api.py'로 실행 시 자식 폴더 OCR 수행 후 JSON 생성
    """
    try:
        print("[INFO] Running as standalone script...")
        if not os.path.exists(CROPPED_IMAGES_DIR):
            raise FileNotFoundError(
                f"[ERROR] CROPPED_IMAGES_DIR not found: {CROPPED_IMAGES_DIR}"
            )

        # 자식 폴더 리스트
        subfolders = [
            os.path.join(CROPPED_IMAGES_DIR, folder)
            for folder in os.listdir(CROPPED_IMAGES_DIR)
            if os.path.isdir(os.path.join(CROPPED_IMAGES_DIR, folder))
        ]
        if not subfolders:
            raise FileNotFoundError(
                "[ERROR] No subfolders found in CROPPED_IMAGES_DIR."
            )

        # 결과 저장
        folder_results = {}

        for subfolder in sorted(subfolders):
            print(f"[INFO] Processing folder: {subfolder}")

            # 이미지 파일 리스트 (오름차순 정렬)
            image_paths = [
                os.path.join(subfolder, fname)
                for fname in sorted(os.listdir(subfolder))
                if fname.lower().endswith((".png", ".jpg", ".jpeg"))
            ]

            if not image_paths:
                print(f"[WARN] No images found in {subfolder}. Skipping...")
                continue

            # OCR 수행
            folder_texts = perform_ocr_on_cropped_images(
                image_paths=image_paths,
                model=ocr_model,
                tokenizer=ocr_tokenizer,
                image_processor=ocr_processor,
                image_size=384,
            )

            # 폴더 이름을 키로 결과 저장
            folder_name = os.path.basename(subfolder)
            folder_results[folder_name] = " ".join(folder_texts).strip()

        # 최종 결과 JSON 생성 및 저장
        result = {
            "cropped_images_dir": CROPPED_IMAGES_DIR,
            "ocr_results": folder_results,
        }
        output_json_path = os.path.join(RESULTS_DIR, "ocr_results_standalone.json")
        with open(output_json_path, "w", encoding="utf-8") as json_file:
            json.dump(result, json_file, ensure_ascii=False, indent=4)

        print(f"[INFO] Standalone OCR results saved to: {output_json_path}")

    except Exception as e:
        print(f"[ERROR] Standalone execution failed: {e}")
    # 임시 디렉토리 정리
    # finally:
    # if os.path.exists(CROPPED_IMAGES_DIR):
    # shutil.rmtree(CROPPED_IMAGES_DIR)
    # print(f"[INFO] Temporary directory {CROPPED_IMAGES_DIR} has been cleaned up.")

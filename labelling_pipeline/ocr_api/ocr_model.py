import os
import json
from PIL import Image
from transformers import VisionEncoderDecoderModel, AutoTokenizer, AutoImageProcessor
from typing import List


def ensure_preprocessor_config_if_missing(model_dir: str):
    """
    모델 디렉토리에 'preprocessor_config.json'이 없을 경우 기본 설정 생성
    """
    preproc_json_path = os.path.join(model_dir, "preprocessor_config.json")

    if os.path.exists(preproc_json_path):
        return  # 이미 파일이 존재하면 건너뜀

    print("[WARN] Missing 'preprocessor_config.json'. Creating default config...")

    default_config = {
        "model_type": "deit",  # 인코더 구조
        "image_processor_type": "DeiTImageProcessor",
        "do_resize": True,
        "size": 384,
        "image_mean": [0.5, 0.5, 0.5],
        "image_std": [0.5, 0.5, 0.5],
    }

    with open(preproc_json_path, "w", encoding="utf-8") as f:
        json.dump(default_config, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Created 'preprocessor_config.json' at {preproc_json_path}")


def load_ocr_model(model_path: str):
    """
    로컬 경로에서 OCR 모델을 로드하고,
    모델, 토크나이저, 이미지 프로세서를 튜플로 반환한다.
    """
    try:
        print(f"[INFO] Loading OCR model from local path: {model_path}")

        if not os.path.exists(model_path):
            print(f"[ERROR] Model path does not exist: {model_path}")
            return None, None, None

        # preprocessor_config.json 확인 및 생성
        ensure_preprocessor_config_if_missing(model_path)

        model = VisionEncoderDecoderModel.from_pretrained(model_path)
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        image_processor = AutoImageProcessor.from_pretrained(model_path)
        return model, tokenizer, image_processor
    except Exception as e:
        print(f"[ERROR] Failed to load OCR model from local path: {e}")
        return None, None, None


def perform_ocr_on_cropped_images(
    image_paths: List[str], model, tokenizer, image_processor, image_size: int = 384
):
    """
    크롭된 이미지 리스트를 받아 OCR을 수행한 뒤, 각 이미지를 인식해 얻은 텍스트를 리스트로 반환한다.
    """
    all_texts = []
    for image_path in image_paths:
        try:
            # 이미지 로드 및 리사이즈
            img = Image.open(image_path).convert("RGB")
            img = img.resize((image_size, image_size))

            # 이미지 전처리
            pixel_values = image_processor(images=img, return_tensors="pt").pixel_values

            # OCR 모델 추론
            output_ids = model.generate(pixel_values, max_length=512)
            decoded_text = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[
                0
            ].strip()

            # 크롭된 이미지 각각에서 추출된 텍스트를 리스트에 추가
            all_texts.append(decoded_text)
            print(f"[INFO] Processed {image_path}: {decoded_text}")

        except Exception as e:
            print(f"[ERROR] Failed to process {image_path}: {e}")
            all_texts.append("")  # 오류 발생 시 빈 텍스트 추가

    return all_texts

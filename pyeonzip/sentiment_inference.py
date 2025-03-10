import torch
import torch.nn.functional as F
from transformers import pipeline, AutoTokenizer,  BertForSequenceClassification

import logging

# ✅ 실행 환경 설정 (CUDA 사용 가능 여부 확인)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# # 모델 및 토크나이저 경로
# MODEL_PATH = "/pyeonzip/models/"
# TOKENIZER_PATH = "/pyeonzip/tokenizers/"

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKENIZER_PATH = os.path.join(BASE_DIR, "tokenizers")
MODEL_PATH = os.path.join(BASE_DIR, "models")

# ✅ 학습된 토크나이저 로드
tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_PATH)

# ✅ 감성 분석 모델 로드 (`model.safetensors` 사용)
model =  BertForSequenceClassification.from_pretrained(MODEL_PATH, num_labels=3)
model.resize_token_embeddings(len(tokenizer))

# ✅ 모델을 GPU로 이동 & 평가 모드로 설정
model.to(device)
model.eval()
print("✅ 모델 로드 완료")


def analyze_text(text: str):
    """
    감성 분석 수행 (Softmax 확률 계산 포함)
    :param text: 입력 문장
    :return: {"label": 예측 클래스, "confidence": 신뢰도}
    """
    logging.info(f"Processing text: {text}")
    # ✅ 입력 데이터를 토큰화
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)

    # ✅ 데이터를 GPU로 이동
    inputs = {key: val.to(device) for key, val in inputs.items()}

    # ✅ 모델 예측 수행
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits  # 로짓(logits) 값 추출
        logging.info(f"🔹 [FastAPI] 모델 출력 logits: {logits}")


        # ✅ Softmax 적용하여 확률(Confidence Score) 계산
        probs = F.softmax(logits, dim=-1)
        conf_scores = torch.max(probs, dim=-1).values.cpu().numpy()[0]  # 가장 높은 확률값

        # ✅ 예측 클래스 (가장 높은 확률을 가진 인덱스)
        pred_class = torch.argmax(probs, dim=-1).cpu().numpy()[0]
    logging.info(f"Predicted class: {pred_class}, Confidence: {conf_scores}")

    return {"PosNeg": int(pred_class), "Confidence": float(conf_scores)}
import torch

import logging
from dotenv import load_dotenv
import os
import requests
import time
from huggingface_hub import InferenceClient

from schemas import SentimentRequest


# # ✅ .env 파일 로드
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 파일의 절대 경로
# ROOT_DIR = os.path.dirname(BASE_DIR)  # 한 단계 위 (프로젝트 루트)
# ENV_PATH = os.path.join(ROOT_DIR, ".env")  # .env 파일 경로
# load_dotenv(dotenv_path=ENV_PATH)
load_dotenv()

# ✅ 환경 변수에서 API 키 가져오기
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
print(f"Hugging Face API Key: {HUGGINGFACE_API_KEY}")

# ✅ 실행 환경 설정 (CUDA 사용 가능 여부 확인)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TASTE_REPO = "haeb/klue-bert-base-taste-custom"
COST_REPO = "haeb/klue-bert-base-cost-custom"
TASTE_API_URL = f"https://api-inference.huggingface.co/models/{TASTE_REPO}"
COST_API_URL = f"https://api-inference.huggingface.co/models/{COST_REPO}"
HEADERS = {
    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
    "Content-Type": "application/json"
}

# client = InferenceClient(
#     model=TASTE_REPO,
#     token=HUGGINGFACE_API_KEY,
# )
# ✅ 🔥 로그 설정 추가 (중요)
logging.basicConfig(
    level=logging.INFO,  # 로그 레벨 설정
    format="%(asctime)s - %(levelname)s - %(message)s",  # 로그 포맷
    handlers=[
        logging.StreamHandler()  # 콘솔에 로그 출력
    ]
)

logging.info("✅ Inference module loaded successfully!")

def analyze_taste(request: SentimentRequest):
    try:
        review_text = request.text.strip()
        if not review_text:
            return {"error": "입력된 텍스트가 없습니다."}

        # response = client.text_classification(review_text)
        response_json = None
        for attempt in range(5):
            response = requests.post(
                TASTE_API_URL,
                headers=HEADERS,
                json={"inputs": review_text}
            )

            if response.status_code == 200:
                try:
                    response_json = response.json()
                    if response_json:
                        logging.info(f"response: {response_json}")
                        break  # 🚀 정상 응답이면 루프 탈출
                    else:
                        logging.warning("⚠️ API 응답이 None 입니다. 재시도 중...")
                except requests.exceptions.JSONDecodeError:
                    logging.error("❌ JSON 디코딩 오류 발생. API 응답이 올바르지 않음.")
                break
            elif response.status_code == 503:
                logging.warning(f"🔄 API 재시도 ({attempt + 1}/5) - 상태 코드: 503 (서비스 불가)")
                time.sleep(attempt + 1)
            else:
                logging.error(f"❌ Hugging Face API 오류: {response.status_code} - {response.text}")
                return {"error": f"API 오류: {response.status_code}", "details": response.text}

        # ✅ 응답 중첩 리스트
        if isinstance(response_json, list) and len(response_json) > 0 and isinstance(response_json[0], list):
            response_json = response_json[0]

        # ✅ 가장 높은 점수를 가진 감성 클래스 찾기
        best_result = max(response_json, key=lambda x: x["score"])
        pred_class = int(best_result["label"].split("_")[-1])
        confidence = float(best_result["score"])

        logging.info(f"Processing text: {review_text}")
        logging.info(f"Predicted class: {pred_class}, Confidence: {confidence}")

        return {"PosNeg": pred_class, "Confidence": confidence}

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ API 요청 중 오류 발생: {str(e)}")
        return {"error": f"API 요청 실패: {str(e)}"}

    except Exception as e:
        logging.error(f"❌ 감성 분석 중 오류 발생: {str(e)}")
        return {"error": f"예상치 못한 오류: {str(e)}"}


def analyze_cost(request: SentimentRequest):
    try:
        review_text = request.text.strip()
        if not review_text:
            return {"error": "입력된 텍스트가 없습니다."}

        # response = client.text_classification(review_text)
        response_json = None
        for attempt in range(5):
            response = requests.post(
                COST_API_URL,
                headers=HEADERS,
                json={"inputs": review_text},
                timeout=30
            )

            if response.status_code == 200:
                try:
                    response_json = response.json()
                    if response_json:
                        logging.info(f"response: {response_json}")
                        break  # 🚀 정상 응답이면 루프 탈출
                    else:
                        logging.warning("⚠️ API 응답이 None 입니다. 재시도 중...")
                except requests.exceptions.JSONDecodeError:
                    logging.error("❌ JSON 디코딩 오류 발생. API 응답이 올바르지 않음.")
                break
            elif response.status_code == 503:
                logging.warning(f"🔄 API 재시도 ({attempt + 1}/5) - 상태 코드: 503 (서비스 불가)")
                time.sleep(attempt + 1)
            else:
                logging.error(f"❌ Hugging Face API 오류: {response.status_code} - {response.text}")
                return {"error": f"API 오류: {response.status_code}", "details": response.text}


        # ✅ 응답 중첩 리스트
        if isinstance(response_json, list) and len(response_json) > 0 and isinstance(response_json[0], list):
            response_json = response_json[0]  # 🔥 첫 번째 리스트만 사용

        # ✅ 가장 높은 점수를 가진 감성 클래스 찾기
        best_result = max(response_json, key=lambda x: x["score"])
        pred_class = int(best_result["label"].split("_")[-1])
        confidence = float(best_result["score"])

        logging.info(f"Processing text: {review_text}")
        logging.info(f"Predicted class: {pred_class}, Confidence: {confidence}")

        return {"PosNeg": pred_class, "Confidence": confidence}

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ API 요청 중 오류 발생: {str(e)}")
        return {"error": f"API 요청 실패: {str(e)}"}

    except Exception as e:
        logging.error(f"❌ 감성 분석 중 오류 발생: {str(e)}")
        return {"error": f"예상치 못한 오류: {str(e)}"}

    # # ✅ 입력 데이터를 토큰화
    # inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    #
    # # ✅ 데이터를 GPU로 이동
    # inputs = {key: val.to(device) for key, val in inputs.items()}
    #
    # # ✅ 모델 예측 수행
    # with torch.no_grad():
    #     outputs = model(**inputs)
    #     logits = outputs.logits  # 로짓(logits) 값 추출
    #     logging.info(f"🔹 [FastAPI] 모델 출력 logits: {logits}")
    #
    #     # ✅ Softmax 적용하여 확률(Confidence Score) 계산
    #     probs = F.softmax(logits, dim=-1)
    #     conf_scores = torch.max(probs, dim=-1).values.cpu().numpy()[0]  # 가장 높은 확률값
    #
    #     # ✅ 예측 클래스 (가장 높은 확률을 가진 인덱스)
    #     pred_class = torch.argmax(probs, dim=-1).cpu().numpy()[0]
    # logging.info(f"Predicted class: {pred_class}, Confidence: {conf_scores}")
    #
    # return {"PosNeg": int(pred_class), "Confidence": float(conf_scores)}

# # 모델 및 토크나이저 경로
# MODEL_PATH = "/pyeonzip/models/"
# TOKENIZER_PATH = "/pyeonzip/tokenizers/"

# import os
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# TOKENIZER_PATH = os.path.join(BASE_DIR, "tokenizers")
# MODEL_PATH = os.path.join(BASE_DIR, "models")

# ✅ 학습된 토크나이저 로드
# tokenizer = AutoTokenizer.from_pretrained(TASTE_REPO, use_auth_token=HUGGINGFACE_API_KEY)

# # ✅ 감성 분석 모델 로드 (`model.safetensors` 사용)
# model =  BertForSequenceClassification.from_pretrained(
#     TASTE_REPO,
#     num_labels=3,
#     use_auth_token=HUGGINGFACE_API_KEY,
#     trust_remote_code=True)
# model.resize_token_embeddings(len(tokenizer))
#
# # ✅ 모델을 GPU로 이동 & 평가 모드로 설정
# model.to(device)
# model.eval()
# print("✅ 모델 로드 완료")
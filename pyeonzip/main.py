from typing import List, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from schemas import SentimentRequest, KeywordRequest, KeywordResponse
from sentiment_inference import analyze_taste, analyze_cost
from keyword_inference import extract_keywords

app = FastAPI()

# ✅ CORS 설정 추가 (모든 도메인 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (보안이 필요하면 특정 도메인만 허용 가능)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

logging.basicConfig(level=logging.INFO)


@app.post("/analyze_taste/")
def analyze_review(request: SentimentRequest):
    """
    FastAPI 맛 감성 분석 엔드포인트
    """
    logging.info(f"🔹 Received Sentiment request: {request.text}")
    result = analyze_taste(request)
    logging.info(f"🔹 Response: {result}")
    return result

@app.post("/analyze_cost/")
def analyze_review(request: SentimentRequest):
    """
    FastAPI 가겨 감성 분석 엔드포인트
    """
    logging.info(f"🔹 Received Sentiment request: {request.text}")
    result = analyze_cost(request)
    logging.info(f"🔹 Response: {result}")
    return result


@app.post("/extract_keywords_hf/", response_model=KeywordResponse)
def extract_keywords_hf_api(request: KeywordRequest):
    """
    Hugging Face Inference API 기반 키워드 추출 엔드포인트
    """
    logging.info(f"🔹 Hugging Face API request: {request.review}")
    result = extract_keywords(request)
    logging.info(f"Response: {result}")
    return result

@app.get("/")
def root():
    logging.info("[FASTAPI ALIVE] 서버 정상 작동 중")
    return {"message": "FastAPI Server is Running!"}






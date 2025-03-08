from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from inference import analyze_text
import logging
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

# 감성 분석 모델
class ReviewRequest(BaseModel):
    text: str

@app.post("/analyze/")
def analyze_review(review: ReviewRequest):
    """
    FastAPI 감성 분석 엔드포인트
    """
    logging.info(f"Received request: {review.text}")
    result = analyze_text(review.text)
    logging.info(f"Response: {result}")
    return result

@app.get("/")
def root():
    logging.info("[FASTAPI ALIVE] 서버 정상 작동 중")
    return {"message": "FastAPI Sentiment Analysis is Running!"}



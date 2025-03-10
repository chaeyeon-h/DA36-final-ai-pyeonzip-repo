from pydantic import BaseModel
from typing import List, Tuple

# ✅ 감성 분석 요청 모델
class SentimentRequest(BaseModel):
    text: str

# ✅ 키워드 추출 요청 모델
class KeywordRequest(BaseModel):
    review: str

# ✅ 키워드 추출 응답 모델
class KeywordResponse(BaseModel):
    keybert_keywords: List[Tuple[str, float]]
    top_sim_tags: List[Tuple[str, str, float]]

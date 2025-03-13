from sentence_transformers import util
import logging

from keybert import KeyBERT
from sentence_transformers import SentenceTransformer

from schemas import KeywordRequest, KeywordResponse

# ✅ KeyBERT 모델 초기화
ko_model = SentenceTransformer("intfloat/multilingual-e5-large")
kw_model = KeyBERT(model=ko_model)

# ✅ 키워드 추출 함수
def extract_keywords(request: KeywordRequest) -> KeywordResponse:
    try:
        review_text = request.review.strip()
        if not review_text:
            raise ValueError("❌ 리뷰가 비어 있습니다.")

        logging.info(f"🔹 키워드 추출 요청: {review_text}")

        # ✅ KeyBERT를 활용한 키워드 추출 (로컬에서 실행)
        try:
            keybert_keywords = kw_model.extract_keywords(
                review_text, keyphrase_ngram_range=(1, 2), stop_words=[], top_n=10, diversity=0.5
            )
            logging.info(f"🔹 KeyBERT 키워드 추출 결과: {keybert_keywords}")
        except Exception as e:
            logging.error(f"❌ KeyBERT 키워드 추출 실패: {e}")
            keybert_keywords = []

        # ✅ 유사 태그 매칭 (로컬 임베딩 사용)
        predefined_tags = ['간편한', '선물용', '간식용', '아이들용', '야식', '술안주', '식사대용','아침대용', '반찬용', '해장용', '분식', '홈파티', '홈카페',
                           '깔끔한', '고급스러운', '새로운', '부족한', '푸짐한', '포만감', '신선한', '가성비', '재구매', '고자극', '다이어트', '무첨가', '건강한',
                           '저칼로리', '무가당', '저당', '대체당', '냉동', '전자레인지', '귀여운', '딱딱한', '알찬구성', '바삭한', '미니사이즈', '빅사이즈',
                           '개별포장', '휴대성', '대용량', '불편한', '호불호', '유명템', '겨울철간식', '달달한', '기름진', '고소한', '자극적인', '짭짤한', '짠맛',
                           '찐한', '진한', '매운', '씁쓸한', '고급스러운', '담백한', '부드러운', '퍽퍽한', '상큼한', '건강한', '슴슴한', '마라', '쫄깃쫄깃한',
                           '꾸덕한', '딱딱한', '마늘향', '밍밍한', '묵직한', '구수한', '쫀득한', '눅눅한', '바삭한', '민초맛', '불맛', '육즙', '촉촉한', '매콤한',
                           '추억의맛', '단짠', '겉바속촉', '시원한', '감칠맛', '촉촉한', '맵찔이', '치즈', '고슬고슬한', '텁텁한', '비린', '맛없는', '얼얼한']

        # ✅ 사전 정의된 태그 임베딩 (로컬에서 실행)
        tag_embeddings = ko_model.encode(predefined_tags, convert_to_tensor=True)

        # ✅ 추출된 키워드 임베딩 (로컬에서 실행)
        extracted_keywords = [kw[0] for kw in keybert_keywords]
        keyword_embeddings = ko_model.encode(extracted_keywords, convert_to_tensor=True)

        # ✅ 코사인 유사도 계산
        similarity_scores = util.pytorch_cos_sim(keyword_embeddings, tag_embeddings)

        # ✅ 유사도가 높은 태그 매칭 후 top_n개만 추출
        top_n = 5
        top_sim_tags = sorted(
            [
            (extracted_keywords[i], predefined_tags[j], similarity_scores[i][j].item())
            for i in range(len(extracted_keywords))
            for j in range(len(predefined_tags))
            if similarity_scores[i][j] >= 0.85
        ],
            key=lambda x: x[2],
            reverse=True
        )[:top_n]

        return KeywordResponse(keybert_keywords=keybert_keywords, top_sim_tags=top_sim_tags)

    except Exception as e:
        logging.error(f"❌ [ERROR] 키워드 추출 중 오류 발생: {str(e)}")
        return KeywordResponse(keybert_keywords=[], top_sim_tags=[])

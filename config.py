"""
프로젝트 전역 설정값을 모아두는 모듈.
API 키처럼 민감한 값은 .env 파일에서 불러온다 (코드에 직접 하드코딩하지 않음).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── 네이버 검색 API 키 ────────────────────────────────
# .env 파일에 아래 두 줄을 추가해서 사용:
#   NAVER_CLIENT_ID=발급받은_아이디
#   NAVER_CLIENT_SECRET=발급받은_시크릿
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# ── 브리핑 관심 키워드 (기본값) ───────────────────────
# 사용자가 "오늘 소식 알려줘"처럼 일반적으로 물어봤을 때
# 이 키워드들을 기준으로 뉴스를 찾는다.
DEFAULT_INTEREST_KEYWORDS = ["오늘 날씨", "건강 뉴스", "지역 소식"]

# ── STT 인식 정확도를 높이기 위한 힌트 문장 ───────────
# 발음이 부정확하거나 소음이 섞여도 이 단어들이 자주 등장한다고
# 미리 알려주면 인식률이 올라간다.
# 주의: 콤마로 나열된 키워드 목록을 쓰면, 무음/잡음 구간에서 모델이
# 실제 음성 대신 이 힌트를 그대로 따라 말하는 환각(hallucination) 현상이
# 발생하기 쉽다. 그래서 실제 발화처럼 자연스러운 문장 형태로 준다.
STT_VOCAB_HINT = "오늘 날씨나 혈압, 건강 뉴스, 코로나, 약 챙기는 시간이 궁금해요."

# ── 확인 루프(재확인) 설정 ────────────────────────────
MAX_CONFIRM_RETRY = 2          # "아니오"/무음/모호한 인식이 반복될 때 최대 재시도 횟수
CONFIRM_RECORD_SECONDS = 3     # "예/아니오" 답변은 짧으므로 3초면 충분
ANSWER_SILENCE_RETRY = 1       # "예/아니오" 답변이 무음으로 잡힐 때, 전체 질문을 되묻기 전에 같은 질문만 다시 시도하는 횟수

# ── 무음 / 모호한 인식 결과 판별 설정 ─────────────────
SILENCE_RMS_THRESHOLD = 300    # 녹음의 RMS 볼륨이 이보다 낮으면 '말이 없었다'고 판단 (마이크 환경에 따라 조정 필요)
MIN_QUESTION_LENGTH = 2        # 인식된 텍스트가 이보다 짧으면 의미 있는 질문으로 보지 않음
HINT_ECHO_SIMILARITY = 0.6     # STT_VOCAB_HINT와 이 비율 이상 유사하면 힌트를 그대로 따라 말한 환각으로 판단

# ── 일반 녹음/모델 설정 ───────────────────────────────
RECORD_SECONDS = 15
SAMPLE_RATE = 16000
MODEL_NAME = "gpt-5.6-luna"

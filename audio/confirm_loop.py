"""
STT로 인식한 내용이 실제로 맞는지 음성으로 재확인하는 모듈.
발음이 부정확하거나 소음이 섞여 잘못 인식된 채로 검색이 실행되는 것을
막기 위한 안전장치.

흐름:
  1) 질문을 녹음하고 텍스트로 변환
  2) "OOO 라고 하신 게 맞으신가요?" 를 음성으로 되물음
  3) "예/아니오" 답변을 녹음해서 판별
  4) "아니오"면 처음부터 다시 (최대 MAX_CONFIRM_RETRY회)
"""
from pathlib import Path
from typing import Optional

from .audio_io import record_audio_to_wav, play_mp3, is_silence
from core import call_tts
from config import MAX_CONFIRM_RETRY, CONFIRM_RECORD_SECONDS, ANSWER_SILENCE_RETRY
from .stt_pipeline import transcribe_clean, is_meaningless

_AFFIRM_WORDS = ("예", "네", "맞아", "맞습니다", "응", "어")
_NEGATIVE_WORDS = ("아니오", "아니요", "아니야", "틀려", "아니")


def _is_affirmative(text: str) -> bool:
    return any(w in text for w in _AFFIRM_WORDS)


def _is_negative(text: str) -> bool:
    return any(w in text for w in _NEGATIVE_WORDS)


def _ask_yes_no(question_audio_path: Path, answer_audio_path: Path, question_text: str) -> str:
    """질문을 음성으로 재생하고, 사용자의 짧은 답변을 텍스트로 반환한다.

    답변 녹음이 무음이면(마이크 타이밍 문제 등) 전체 요청을 처음부터 다시 묻는 대신,
    같은 예/아니오 질문만 다시 들려주고 재시도한다.
    """
    call_tts(question_audio_path, question_text)
    play_mp3(str(question_audio_path))

    for attempt in range(ANSWER_SILENCE_RETRY + 1):
        record_audio_to_wav(answer_audio_path, duration=CONFIRM_RECORD_SECONDS)

        if is_silence(answer_audio_path):
            print(f"[확인 답변 {attempt + 1}회차] 무음으로 판단")
            if attempt < ANSWER_SILENCE_RETRY:
                call_tts(answer_audio_path, "예 또는 아니오로 답해주세요.")
                play_mp3(str(answer_audio_path))
            continue

        return transcribe_clean(str(answer_audio_path))

    return ""


def _notify(audio_path: Path, text: str) -> None:
    """재시도를 요청하는 안내 음성을 재생한다."""
    call_tts(audio_path, text)
    play_mp3(str(audio_path))


def get_confirmed_text(question_audio_path: Path, confirm_audio_path: Path,
                        answer_audio_path: Path) -> Optional[str]:
    """
    사용자 질문을 녹음 → 인식 → 재확인까지 처리한다.
    무음이거나 인식 결과가 모호(짧음/힌트 환각)하면 재확인 없이 바로 재녹음을 요청한다.
    확인되면 인식된 텍스트를, 재시도 횟수를 초과하면 None을 반환한다.
    """
    for attempt in range(MAX_CONFIRM_RETRY + 1):
        record_audio_to_wav(question_audio_path)

        if is_silence(question_audio_path):
            print(f"[{attempt + 1}회차] 무음으로 판단")
            _notify(confirm_audio_path, "아무 말도 들리지 않았어요. 다시 한번 말씀해주세요.")
            continue

        recognized_text = transcribe_clean(str(question_audio_path))
        print(f"[인식 결과 {attempt + 1}회차]:", recognized_text)

        if is_meaningless(recognized_text):
            print(f"[{attempt + 1}회차] 모호한 인식 결과로 판단")
            _notify(confirm_audio_path, "질문을 잘 이해하지 못했어요. 다시 한번 또박또박 말씀해주세요.")
            continue

        confirm_question = f"{recognized_text} 라고 하신 게 맞으신가요? 맞으면 예, 다시 말씀하시려면 아니오 라고 해주세요."
        answer_text = _ask_yes_no(confirm_audio_path, answer_audio_path, confirm_question)
        print("[확인 답변]:", answer_text)

        if _is_affirmative(answer_text):
            return recognized_text

        # "아니오"이거나 예/아니오 어느 쪽도 아니면 재시도
        continue

    return None

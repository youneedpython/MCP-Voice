"""
녹음된 내용이 실제로 의미 있는 발화인지 걸러내는 모듈.

예전에는 인식할 때마다 "OOO 라고 하신 게 맞으신가요?"로 예/아니오를 되물었지만,
매번 확인을 거치면 대화 흐름이 끊겨서 없앴다. 대신:
  1) 무음이면(마이크에 아무 소리도 안 잡히면) 다시 말해달라고 요청
  2) 인식은 됐지만 너무 짧거나 STT가 힌트 문장을 그대로 따라 말한 환각이면
     역시 다시 말해달라고 요청
  3) 그 외에는 바로 신뢰하고 다음 단계로 넘어간다 — 잘못 이해했더라도
     대화 맥락이 유지되므로 다음 턴에 "아니 그게 아니라~"처럼 자연스럽게 정정 가능
"""
from pathlib import Path
from typing import Optional

from .audio_io import record_audio_to_wav, play_mp3
from core import call_tts
from config import MAX_CONFIRM_RETRY
from .stt_pipeline import transcribe_clean, is_meaningless


def _notify(audio_path: Path, text: str) -> None:
    """재시도를 요청하는 안내 음성을 재생한다."""
    call_tts(audio_path, text)
    play_mp3(str(audio_path))


def get_confirmed_text(question_audio_path: Path, confirm_audio_path: Path) -> Optional[str]:
    """
    질문을 녹음하고 인식한다. 무음이거나 인식 결과가 모호(짧음/힌트 환각)하면
    다시 말해달라고 요청한다. 정상 인식되면 재확인 없이 바로 그 텍스트를 반환한다.
    재시도 횟수를 초과하면 None을 반환한다.
    """
    for attempt in range(MAX_CONFIRM_RETRY + 1):
        speech_detected = record_audio_to_wav(question_audio_path)

        if not speech_detected:
            print(f"[{attempt + 1}회차] 무음으로 판단")
            _notify(confirm_audio_path, "아무 말도 들리지 않았어요. 다시 한번 말씀해주세요.")
            continue

        recognized_text = transcribe_clean(str(question_audio_path))
        print(f"[인식 결과 {attempt + 1}회차]:", recognized_text)

        if is_meaningless(recognized_text):
            print(f"[{attempt + 1}회차] 모호한 인식 결과로 판단")
            _notify(confirm_audio_path, "질문을 잘 이해하지 못했어요. 다시 한번 또박또박 말씀해주세요.")
            continue

        return recognized_text

    return None

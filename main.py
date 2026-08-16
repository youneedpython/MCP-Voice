"""
음성 정보 브리핑 비서 — 진입점

흐름: 녹음 → (노이즈 제거 + STT) → 확인 루프 → MCP 에이전트(네이버 검색 + 파일시스템)
      → 응답 요약 → TTS → 재생
"""
import asyncio
import os
import shutil
from pathlib import Path

from audio import play_mp3, get_confirmed_text
from core import call_tts
from agent import get_briefing

BASE_DIR = Path(__file__).parent

# 이 단어가 확정된 요청에 포함되면 대화를 마치고 프로그램을 종료한다.
_EXIT_WORDS = ("종료", "그만", "끝낼래", "끝내줘", "그만할래", "안녕히")

# 연속으로 이 횟수만큼 오류가 발생하면(예: MCP 서버 장애) 무한 반복을 막기 위해 종료한다.
_MAX_CONSECUTIVE_ERRORS = 3


def _speak(speech_path: Path, text: str) -> None:
    call_tts(speech_path, text)
    play_mp3(str(speech_path))


def _is_exit_intent(text: str) -> bool:
    return any(word in text for word in _EXIT_WORDS)


def main() -> None:
    question_audio = BASE_DIR / "speech_question.wav"
    confirm_audio = BASE_DIR / "speech_confirm.mp3"
    answer_audio = BASE_DIR / "speech_answer.wav"
    response_audio = BASE_DIR / "speech_response.mp3"
    results_dir = os.path.join(str(BASE_DIR), "results")

    _speak(response_audio, "안녕하세요. 궁금한 걸 말씀해주세요. 대화를 마치시려면 종료라고 말씀해주세요.")

    # 이전 턴까지의 대화 이력. 매 턴 이 리스트를 에이전트에 그대로 넘겨야
    # "그거", "아까 그건" 같은 이어지는 질문에도 맥락을 유지한 채 답할 수 있다.
    conversation_history: list = []
    consecutive_errors = 0
    while True:
        try:
            confirmed_text = get_confirmed_text(question_audio, confirm_audio, answer_audio)

            if confirmed_text is None:
                print("확인 재시도 횟수를 초과했습니다.")
                _speak(response_audio, "죄송해요, 잘 알아듣지 못했어요. 다시 한번 말씀해주세요.")
                continue

            if _is_exit_intent(confirmed_text):
                print("대화를 종료합니다.")
                _speak(response_audio, "네, 대화를 마칠게요. 안녕히 계세요.")
                break

            print("확정된 요청:", confirmed_text)
            conversation_history.append({"role": "user", "content": confirmed_text})
            output_text, conversation_history = asyncio.run(
                get_briefing(conversation_history, results_dir)
            )
            print("응답:", output_text)

            _speak(response_audio, output_text)
            consecutive_errors = 0

        except Exception as e:
            print(f"오류 발생: {e}")
            consecutive_errors += 1

            if consecutive_errors >= _MAX_CONSECUTIVE_ERRORS:
                _speak(response_audio, "죄송해요, 문제가 계속 발생해서 프로그램을 종료할게요.")
                break

            _speak(response_audio, "죄송해요, 처리 중 문제가 생겼어요. 다시 한번 말씀해주세요.")


if __name__ == "__main__":
    if not shutil.which("npx"):
        raise RuntimeError("npx is not installed. Please install it with `npm install -g npx`.")
    main()

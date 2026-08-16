from pathlib import Path
from openai import OpenAI
from datetime import datetime

client = OpenAI()

current_date = datetime.now().strftime('%Y%m%d_%H%M%S')

# API연결하는 함수를 만듬. 입력값은 오디오 파일 경로, 입력 텍스트, 모델명은 gpt-4o-mini-tts
# 실패를 여기서 삼키면 호출한 쪽이 실패를 모른 채 이전 mp3를 그대로 재생하게 되므로,
# 예외를 그대로 올려서 호출한 쪽의 오류 처리(재시도/안내 등)로 넘긴다.
def call_tts(speech_file_path: str, input_text: str, model_name: str = "gpt-4o-mini-tts") -> None:
    with client.audio.speech.with_streaming_response.create(
        model=model_name,
        voice="alloy",
        input=input_text
        ) as response:
            response.stream_to_file(speech_file_path)

if __name__ == "__main__":
    speech_file_path = Path(__file__).parent / f"speech_tts_{current_date}.mp3"
    input_text = "인공지능에 대해 한 줄로 알려 줘"
    call_tts(speech_file_path, input_text)
    print("요청:", input_text)
    print("응답:", speech_file_path)

from pathlib import Path
from openai import OpenAI
from datetime import datetime

client = OpenAI()

current_date = datetime.now().strftime('%Y%m%d_%H%M%S')

# API연결하는 함수를 만듬. 입력값은 오디오 파일 경로, 입력 텍스트, 모델명은 gpt-4o-mini-tts
def call_tts(speech_file_path: str, input_text: str, model_name: str = "gpt-4o-mini-tts") -> str:
    try:
        with client.audio.speech.with_streaming_response.create(
            model=model_name,
            voice="alloy",
            input=input_text
            ) as response:
                response.stream_to_file(speech_file_path)
    
    except Exception as e:
        print(f"[ERROR] ChatGPT 호출 중 예외 발생: {e}")
        return "오류가 발생했습니다."

if __name__ == "__main__":
    speech_file_path = Path(__file__).parent / f"speech_tts_{current_date}.mp3"
    input_text = "인공지능에 대해 한 줄로 알려 줘"
    call_tts(speech_file_path, input_text)
    print("요청:", input_text)
    print("응답:", speech_file_path)

from openai import OpenAI

client = OpenAI()

# API연결하는 함수를 만듬. 입력값은 오디오 파일 경로, 모델명은 gpt-4o-mini-transcribe
# prompt: 자주 등장할 단어를 미리 알려주면 인식률이 올라감 (STT 힌트)
def call_transcribe(audio_path: str, model_name: str = "gpt-4o-mini-transcribe",
                     prompt: str = "") -> str:
    try:
        audio_file = open(audio_path, "rb")
        kwargs = {"model": model_name, "file": audio_file}
        if prompt:
            kwargs["prompt"] = prompt
        transcript = client.audio.transcriptions.create(**kwargs)
        return transcript.text

    except Exception as e:
        print(f"[ERROR] STT 호출 중 예외 발생: {e}")
        return "오류가 발생했습니다."


if __name__ == "__main__":
    audio_path = "speech_transcribe.mp3"
    output_text = call_transcribe(audio_path)
    print("요청:", audio_path)
    print("응답:", output_text)

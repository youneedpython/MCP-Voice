from openai import OpenAI

client = OpenAI()

# API연결하는 함수를 만듬. 입력값은 문자열, 모델명은 gpt-5.6-luna
def call_chatgpt(input_text: str, model_name: str = "gpt-5.6-luna") -> str:
    # 통신 오류에 대비하기 위한 오류처리
    try:
        response = client.responses.create(
            model=model_name,
            input= input_text
        )
        
        return response.output_text

    # 통신 오류에 대비하기 위한 오류처리
    except Exception as e:
        print(f"[ERROR] ChatGPT 호출 중 예외 발생: {e}")
        return "오류가 발생했습니다."


# 직접 실행인 경우만 실행. 전체 흐름을 제어하기 위한 영역
if __name__ == "__main__":
    input_text = "인공지능에 대해 한 줄로 알려 줘"
    # chatgpt 통신 처리한 후 output_text에 저장
    output_text = call_chatgpt(input_text)
    # 요청과 응답을 출력력
    print("요청:", input_text)
    print("응답:", output_text)

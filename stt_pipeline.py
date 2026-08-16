"""
녹음된 오디오를 텍스트로 바꾸는 단계를 담당하는 모듈.
1) 배경 소음 제거 (noisereduce가 설치돼 있으면 적용, 없으면 건너뜀)
2) STT 변환 시 자주 등장할 단어를 prompt 힌트로 넘겨 인식률을 높임
"""
import difflib

from scipy.io import wavfile

from config import HINT_ECHO_SIMILARITY, MIN_QUESTION_LENGTH, STT_VOCAB_HINT
from core import call_transcribe

try:
    import noisereduce as nr
    _HAS_NOISEREDUCE = True
except ImportError:
    # 선택 라이브러리이므로 없어도 프로그램이 죽지 않게 처리.
    # pip install noisereduce 로 설치하면 자동으로 활성화된다.
    _HAS_NOISEREDUCE = False


def denoise_wav(audio_path: str) -> None:
    """wav 파일의 배경 소음을 줄여서 같은 경로에 덮어쓴다."""
    if not _HAS_NOISEREDUCE:
        return
    rate, data = wavfile.read(audio_path)
    reduced = nr.reduce_noise(y=data, sr=rate)
    wavfile.write(audio_path, rate, reduced.astype(data.dtype))


def transcribe_clean(audio_path: str) -> str:
    """노이즈 제거 후 STT로 변환된 텍스트를 반환한다."""
    denoise_wav(audio_path)
    return call_transcribe(audio_path, prompt=STT_VOCAB_HINT)


def is_meaningless(text: str) -> bool:
    """빈 응답, 너무 짧은 응답, STT_VOCAB_HINT를 그대로 따라 말한 환각 응답을 걸러낸다."""
    cleaned = text.strip()
    if len(cleaned) < MIN_QUESTION_LENGTH:
        return True

    similarity = difflib.SequenceMatcher(None, cleaned, STT_VOCAB_HINT).ratio()
    return similarity >= HINT_ECHO_SIMILARITY

"""
마이크 녹음과 mp3 재생만 담당하는 모듈.
다른 로직(STT, 확인 루프 등)은 이 모듈을 가져다 쓰기만 하고,
녹음/재생의 세부 구현은 이 파일 안에서만 관리한다.
"""
from pathlib import Path

import numpy as np
import pygame
import sounddevice as sd
import time
from scipy.io.wavfile import read, write

from config import RECORD_SECONDS, SAMPLE_RATE, SILENCE_RMS_THRESHOLD


def record_audio_to_wav(audio_path: Path, duration: int = RECORD_SECONDS,
                         sample_rate: int = SAMPLE_RATE) -> None:
    """마이크로 duration초간 녹음해서 wav 파일로 저장한다."""
    # 직전에 TTS 재생이 있었다면 출력 장치에서 입력 장치로 전환될 시간을 잠깐 준다.
    # (재생 직후 바로 녹음을 시작하면 초반 구간이 제대로 안 잡히는 경우가 있다)
    time.sleep(0.3)
    print(f"{duration}초간 말해주세요.")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate,
                    channels=1, dtype="int16")
    sd.wait()
    write(audio_path, sample_rate, audio)
    print("녹음 완료")


def is_silence(audio_path: Path, threshold: int = SILENCE_RMS_THRESHOLD,
               window_ms: int = 300) -> bool:
    """녹음된 오디오가 사실상 무음(마이크 미인식, 묵음 등)인지 RMS 볼륨으로 판별한다.

    녹음 전체의 평균 RMS로 판단하면, "네"처럼 짧게 말하고 나머지가 조용한 경우
    평균이 희석되어 실제로 말을 했는데도 무음으로 오판될 수 있다.
    그래서 전체를 window_ms 단위 구간으로 나눠 그중 가장 큰 RMS를 기준으로 삼는다.

    무음/잡음 구간을 STT로 넘기면 모델이 힌트 텍스트를 그대로 따라 말하는
    환각 현상이 생기기 쉬우므로, API를 호출하기 전에 먼저 걸러낸다.
    """
    rate, data = read(audio_path)
    data = data.astype(np.float64)

    window_size = max(1, int(rate * window_ms / 1000))
    max_rms = 0.0
    for start in range(0, len(data), window_size):
        chunk = data[start:start + window_size]
        if len(chunk) == 0:
            continue
        chunk_rms = np.sqrt(np.mean(chunk ** 2))
        max_rms = max(max_rms, chunk_rms)

    return max_rms < threshold


def play_mp3(file_path: str) -> None:
    """mp3 파일을 재생하고, 재생이 끝날 때까지 대기한다."""
    # 재생마다 init()을 반복하면(quit 없이) 대화가 길어질수록 오디오 장치 핸들이
    # 쌓여서 녹음 품질이 떨어질 수 있으므로, 아직 초기화되지 않았을 때만 초기화한다.
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

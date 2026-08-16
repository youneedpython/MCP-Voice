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
from scipy.io.wavfile import write

from config import RECORD_SECONDS, SAMPLE_RATE, SILENCE_RMS_THRESHOLD, SILENCE_STOP_SECONDS

_CHUNK_SECONDS = 0.1  # 이 단위로 마이크를 읽으며 침묵 여부를 확인한다.


def record_audio_to_wav(audio_path: Path, max_duration: int = RECORD_SECONDS,
                         sample_rate: int = SAMPLE_RATE,
                         silence_stop_seconds: float = SILENCE_STOP_SECONDS,
                         silence_threshold: int = SILENCE_RMS_THRESHOLD) -> bool:
    """마이크로 녹음해서 wav 파일로 저장한다.

    사람 대화처럼, 말이 시작된 뒤 silence_stop_seconds 이상 조용해지면 자동으로
    녹음을 끝낸다. max_duration은 계속 말이 이어질 때를 대비한 최대 녹음 시간(안전장치)이다.
    반환값은 녹음 중 실제로 말소리(침묵 임계값 이상)가 감지됐는지 여부다.
    """
    # 직전에 TTS 재생이 있었다면 출력 장치에서 입력 장치로 전환될 시간을 잠깐 준다.
    # (재생 직후 바로 녹음을 시작하면 초반 구간이 제대로 안 잡히는 경우가 있다)
    time.sleep(0.3)
    print(f"말씀해주세요. (최대 {max_duration}초, 말을 마치면 자동으로 넘어갑니다)")

    chunk_frames = max(1, int(sample_rate * _CHUNK_SECONDS))
    max_chunks = max(1, int(max_duration / _CHUNK_SECONDS))
    silence_chunks_needed = max(1, int(silence_stop_seconds / _CHUNK_SECONDS))

    chunks = []
    speech_started = False
    silence_run = 0

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16") as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(chunk_frames)
            chunks.append(chunk.copy())

            rms = np.sqrt(np.mean(chunk.astype(np.float64) ** 2))
            if rms >= silence_threshold:
                speech_started = True
                silence_run = 0
            elif speech_started:
                silence_run += 1
                if silence_run >= silence_chunks_needed:
                    break

    audio = np.concatenate(chunks, axis=0) if chunks else np.zeros((0, 1), dtype="int16")
    write(audio_path, sample_rate, audio)
    print("녹음 완료")
    return speech_started


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

    # load()는 재생이 끝나도 파일 핸들을 계속 쥐고 있어서, 같은 파일명에 새 TTS
    # 결과를 덮어쓰려 하면 Windows에서 PermissionError가 난다. 재생이 끝나면 바로
    # 언로드해서 다음 call_tts()가 같은 경로에 다시 쓸 수 있게 한다.
    pygame.mixer.music.unload()

"""Small ctypes bridge to RNNoise for 48 kHz mono microphone audio."""
import ctypes
from pathlib import Path
import sys

import numpy as np


class RNNoiseSuppressor:
    frame_size = 480

    def __init__(self):
        root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        self.library = ctypes.CDLL(str(root / "rnnoise.dll"))
        self.library.rnnoise_create.argtypes = [ctypes.c_void_p]
        self.library.rnnoise_create.restype = ctypes.c_void_p
        self.library.rnnoise_destroy.argtypes = [ctypes.c_void_p]
        self.library.rnnoise_process_frame.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_float),
            ctypes.POINTER(ctypes.c_float),
        ]
        self.library.rnnoise_process_frame.restype = ctypes.c_float
        self.state = self.library.rnnoise_create(None)
        if not self.state:
            raise RuntimeError("RNNoise could not initialize.")

    def process(self, audio):
        audio = np.asarray(audio, dtype=np.float32).reshape(-1)
        if audio.size % self.frame_size:
            padded = np.pad(audio, (0, self.frame_size - audio.size % self.frame_size))
        else:
            padded = audio
        frames = (padded * 32768.0).clip(-32768, 32767).astype(np.float32)
        for start in range(0, frames.size, self.frame_size):
            frame = np.ascontiguousarray(frames[start:start + self.frame_size])
            pointer = frame.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            self.library.rnnoise_process_frame(self.state, pointer, pointer)
            frames[start:start + self.frame_size] = frame
        return (frames[:audio.size] / 32768.0).astype(np.float32, copy=False)

    def close(self):
        if self.state:
            self.library.rnnoise_destroy(self.state)
            self.state = None

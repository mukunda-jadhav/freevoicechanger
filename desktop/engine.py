"""Streaming adapter for the MIT-licensed RVC real-time inference engine."""
from types import SimpleNamespace
import numpy as np
import torch
import torch.nn.functional as F
from torchaudio.transforms import Resample
from infer.rtrvc import RVC


class VoiceEngine:
    rate = 48000
    block = 24000

    def __init__(self, device="cuda", pitch=12):
        torch.set_num_threads(2)
        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("NVIDIA GPU is unavailable. Select CPU instead.")
        self.device = torch.device(device)
        self.rvc = RVC(pitch, 0, "assets/weights/female.pth",
                       "assets/weights/female.index", 0.5,
                       SimpleNamespace(device=self.device, is_half=device == "cuda"))
        if getattr(self.rvc, "net_g", None) is None:
            raise RuntimeError("The voice model could not be loaded. See the application log.")
        if hasattr(self.rvc, "index"):
            self.rvc.index.nprobe = min(8, self.rvc.index.nlist)
        self.zc = self.rate // 100
        self.overlap = 1920
        self.search = 480
        self.context = 48000
        self.wave = torch.zeros(self.context + self.block + self.overlap + self.search, device=self.device)
        self.wave16 = torch.zeros(self.wave.numel() // 3, device=self.device)
        self.tail = torch.zeros(self.overlap, device=self.device)
        self.fade = torch.linspace(0, 1, self.overlap, device=self.device).square()
        self.to16 = Resample(48000, 16000).to(self.device)
        self.to48 = Resample(self.rvc.tgt_sr, 48000).to(self.device)
        self.kernel = torch.ones(1, 1, self.overlap, device=self.device)

    @torch.inference_mode()
    def process(self, audio, pitch=12):
        self.rvc.change_key(pitch)
        self.wave[:-self.block] = self.wave[self.block:].clone()
        self.wave[-self.block:] = torch.as_tensor(audio, dtype=torch.float32, device=self.device)
        self.wave16[:-8000] = self.wave16[8000:].clone()
        self.wave16[-8160:] = self.to16(self.wave[-self.block - 960:])[160:]
        converted = self.rvc.infer(self.wave16, 8000, 100, 55, "rmvpe")
        converted = self.to48(converted)
        correlation_input = converted[:self.overlap + self.search][None, None]
        numerator = F.conv1d(correlation_input, self.tail[None, None])
        denominator = torch.sqrt(F.conv1d(correlation_input.square(), self.kernel) + 1e-8)
        offset = int(torch.argmax(numerator / denominator).item())
        converted = converted[offset:]
        converted[:self.overlap] = converted[:self.overlap] * self.fade + self.tail * (1 - self.fade)
        self.tail.copy_(converted[self.block:self.block + self.overlap])
        return converted[:self.block].clamp(-0.98, 0.98).cpu().numpy().copy()

    def close(self):
        self.rvc = None
        if self.device.type == "cuda":
            torch.cuda.empty_cache()

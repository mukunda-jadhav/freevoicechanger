"""FreeVoice desktop: one ready-made female voice, no training."""
import collections
import logging
import os
from pathlib import Path
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
os.chdir(ROOT)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["RVC_CUDA_GRAPH"] = "0"
LOGDIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "FreeVoice"
LOGDIR.mkdir(exist_ok=True)
logging.basicConfig(filename=LOGDIR / "freevoice.log", level=logging.INFO)
if sys.stdout is None:
    sys.stdout = open(LOGDIR / "engine.log", "a", encoding="utf-8", buffering=1)
if sys.stderr is None:
    sys.stderr = sys.stdout


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FreeVoice — Female voice")
        self.geometry("660x620")
        self.minsize(620, 580)
        self.configure(bg="#101827")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 11), background="#101827", foreground="#F3F4F6")
        style.configure("TButton", padding=12, background="#7253D6")
        style.map("TButton", background=[("active", "#8566E5"), ("disabled", "#344155")])
        style.configure("TCombobox", fieldbackground="#FFFFFF", foreground="#111827", padding=8)
        style.configure("TScale", background="#101827")
        box = ttk.Frame(self, padding=28)
        box.pack(fill="both", expand=True)
        ttk.Label(box, text="FreeVoice", font=("Segoe UI", 28, "bold")).pack(anchor="w")
        ttk.Label(box, text="One female voice. All processing stays on this PC.",
                  wraplength=580).pack(anchor="w", pady=(4, 20))
        self.input = self.combo(box, "Microphone")
        self.output = self.combo(box, "Output — headphones or virtual cable")
        ttk.Label(box, text="For calls: select the cable here, then its microphone in your calling app.",
                  wraplength=570).pack(anchor="w", pady=(0, 12))
        self.device = self.combo(box, "Processing")
        self.device["values"] = ("NVIDIA GPU — faster", "CPU — no GPU use")
        self.device.current(0)
        self.pitch = tk.DoubleVar(value=12)
        self.pitch_value = 12
        self.pitch_label = ttk.Label(box, text="Pitch shift: +12 semitones")
        self.pitch_label.pack(anchor="w")
        self.slider = ttk.Scale(box, from_=0, to=18, variable=self.pitch, command=self.update_pitch)
        self.slider.pack(fill="x", pady=(6, 16))
        self.status = tk.StringVar(value="Stopped. Choose your devices, then press Start.")
        ttk.Label(box, textvariable=self.status, wraplength=570).pack(anchor="w", pady=(0, 16))
        buttons = ttk.Frame(box)
        buttons.pack(fill="x")
        self.start_button = ttk.Button(buttons, text="Start voice changer", command=self.start)
        self.start_button.pack(side="left", fill="x", expand=True)
        self.stop_button = ttk.Button(buttons, text="Stop", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=(10, 0))
        self.refresh_button = ttk.Button(box, text="Refresh audio devices", command=self.refresh)
        self.refresh_button.pack(anchor="w", pady=(12, 6))
        ttk.Label(box, text="Use headphones to avoid feedback. Expect noticeable conversational delay.\n"
                  "Voice: VCTK p231 / Nekochu • No custom training or account required.",
                  wraplength=570, font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 0))
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.worker = None
        self.closing = False
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh()
        self.after(150, self.poll)

    def combo(self, parent, label):
        ttk.Label(parent, text=label).pack(anchor="w")
        widget = ttk.Combobox(parent, state="readonly")
        widget.pack(fill="x", pady=(5, 12))
        return widget

    def update_pitch(self, _=None):
        self.pitch_value = int(round(self.pitch.get()))
        self.pitch_label.configure(text=f"Pitch shift: +{self.pitch_value} semitones")

    def refresh(self):
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            hosts = sd.query_hostapis()
            self.inputs = [(i, f"{d['name']} [{hosts[d['hostapi']]['name']}]")
                           for i, d in enumerate(devices) if d["max_input_channels"] > 0]
            self.outputs = [(i, f"{d['name']} [{hosts[d['hostapi']]['name']}]")
                            for i, d in enumerate(devices) if d["max_output_channels"] > 0]
            for widget, entries, default in ((self.input, self.inputs, sd.default.device[0]),
                                             (self.output, self.outputs, sd.default.device[1])):
                widget["values"] = [name for _, name in entries]
                if entries:
                    widget.current(next((j for j, (i, _) in enumerate(entries) if i == default), 0))
        except Exception as exc:
            self.status.set(f"Audio devices unavailable: {exc}")

    def start(self):
        if self.worker and self.worker.is_alive():
            return
        if self.input.current() < 0 or self.output.current() < 0:
            messagebox.showerror("Choose devices", "Select a microphone and an output device.")
            return
        options = (self.inputs[self.input.current()][0], self.outputs[self.output.current()][0],
                   "cuda" if self.device.current() == 0 else "cpu")
        self.cancel.clear()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.refresh_button.configure(state="disabled")
        for widget in (self.input, self.output, self.device):
            widget.configure(state="disabled")
        self.status.set("Loading female voice… You can press Stop at any time.")
        self.worker = threading.Thread(target=self.run_audio, args=options, daemon=True)
        self.worker.start()

    def run_audio(self, input_id, output_id, device):
        engine = None
        try:
            import numpy as np
            import sounddevice as sd
            from engine import VoiceEngine
            engine = VoiceEngine(device, self.pitch_value)
            if self.cancel.is_set():
                return
            # Warm up before opening the microphone.
            engine.process(np.zeros(engine.block, np.float32), self.pitch_value)
            if self.cancel.is_set():
                return
            incoming = queue.Queue(maxsize=2)
            outgoing = collections.deque()
            lock = threading.Lock()
            overflow = threading.Event()
            channels = min(2, int(sd.query_devices(output_id)["max_output_channels"]))
            def capture(data, frames, timing, status):
                if status:
                    overflow.set()
                try:
                    incoming.put_nowait(data[:, 0].copy())
                except queue.Full:
                    overflow.set()
            def playback(data, frames, timing, status):
                data.fill(0)
                with lock:
                    offset = 0
                    while outgoing and offset < frames:
                        chunk = outgoing[0]
                        count = min(len(chunk), frames - offset)
                        data[offset:offset + count] = chunk[:count, None]
                        offset += count
                        if count == len(chunk):
                            outgoing.popleft()
                        else:
                            outgoing[0] = chunk[count:]
            with sd.OutputStream(device=output_id, samplerate=48000, channels=channels,
                                 dtype="float32", callback=playback, latency="high"), \
                 sd.InputStream(device=input_id, samplerate=48000, blocksize=24000, channels=1,
                                dtype="float32", callback=capture, latency="high"):
                self.events.put(("status", "Live — speak into your microphone."))
                while not self.cancel.is_set():
                    try:
                        audio = incoming.get(timeout=0.2)
                    except queue.Empty:
                        continue
                    before = time.perf_counter()
                    converted = engine.process(audio, self.pitch_value)
                    elapsed = time.perf_counter() - before
                    with lock:
                        if len(outgoing) >= 3:
                            outgoing.clear()
                            overflow.set()
                        outgoing.append(converted)
                    if elapsed > 0.5 or overflow.is_set():
                        self.events.put(("status", f"Processing {elapsed*1000:.0f} ms / 500 ms. "
                                         "Audio may stutter; close heavy apps or try GPU."))
                        overflow.clear()
                    else:
                        self.events.put(("status", f"Live • {elapsed*1000:.0f} ms processing / 500 ms audio • "
                                         "Stop releases the voice engine."))
        except Exception as exc:
            logging.exception("Voice conversion failed")
            self.events.put(("error", str(exc)))
        finally:
            if engine is not None:
                engine.close()
                del engine
            # Tensor references have now been released.
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass
            self.events.put(("done", None))

    def stop(self):
        self.cancel.set()
        self.stop_button.configure(state="disabled")
        self.status.set("Stopping… waiting for the current audio block.")

    def close(self):
        self.closing = True
        if self.worker and self.worker.is_alive():
            self.stop()
        else:
            self.destroy()

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "status" and not self.cancel.is_set():
                    self.status.set(value)
                elif kind == "error":
                    self.status.set(f"Stopped: {value}")
                    if not self.closing:
                        messagebox.showerror("Voice changer stopped", value + f"\n\nLog: {LOGDIR}")
                elif kind == "done":
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    self.refresh_button.configure(state="normal")
                    for widget in (self.input, self.output, self.device):
                        widget.configure(state="readonly")
                    if self.cancel.is_set():
                        self.status.set("Stopped. Microphone and voice engine released.")
                    if self.closing:
                        self.destroy()
                        return
        except queue.Empty:
            pass
        self.after(150, self.poll)


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    App().mainloop()

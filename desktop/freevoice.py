"""FemaleVocal desktop: one ready-made female voice, no training."""
import collections
import logging
import math
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
SEEDVC_ROOT = ROOT / "seedvc_backend" / "seed-vc-realtime"
sys.path.insert(0, str(SEEDVC_ROOT))
os.environ.pop("HF_HUB_OFFLINE", None)
os.environ.pop("TRANSFORMERS_OFFLINE", None)
os.environ["RVC_CUDA_GRAPH"] = "0"
LOGDIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "FemaleVocal"
LOGDIR.mkdir(exist_ok=True)
os.environ.setdefault("HF_HOME", str(LOGDIR / "models"))
logging.basicConfig(filename=LOGDIR / "freevoice.log", level=logging.INFO)
if sys.stdout is None:
    sys.stdout = open(LOGDIR / "engine.log", "a", encoding="utf-8", buffering=1)
if sys.stderr is None:
    sys.stderr = sys.stdout


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FemaleVocal — Live voice changer")
        self.geometry("820x790")
        self.minsize(700, 700)
        self.configure(bg="#0A0F1C")
        self.colors = {
            "background": "#0A0F1C", "surface": "#121B2B", "surface_raised": "#19263A",
            "border": "#29384F", "text": "#F4F6FB", "body": "#C0CAD9",
            "muted": "#91A0B6", "accent": "#A78BFA", "accent_hover": "#B8A5FF",
            "green": "#53D6A0", "amber": "#F0BD68", "red": "#FF8989",
        }
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background=self.colors["background"],
                        foreground=self.colors["text"])
        style.configure("TFrame", background=self.colors["background"])
        style.configure("Card.TFrame", background=self.colors["surface"],
                        relief="solid", borderwidth=1, bordercolor=self.colors["border"])
        style.configure("CardInner.TFrame", background=self.colors["surface"])
        style.configure("Brand.TLabel", font=("Segoe UI Semibold", 15),
                        background=self.colors["background"], foreground=self.colors["text"])
        style.configure("Local.TLabel", font=("Segoe UI", 9, "bold"),
                        background=self.colors["surface_raised"], foreground=self.colors["accent"])
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 25),
                        background=self.colors["background"], foreground=self.colors["text"])
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10),
                        background=self.colors["background"], foreground=self.colors["body"])
        style.configure("CardTitle.TLabel", font=("Segoe UI", 10, "bold"),
                        background=self.colors["surface"], foreground=self.colors["text"])
        style.configure("CardText.TLabel", font=("Segoe UI", 9),
                        background=self.colors["surface"], foreground=self.colors["body"])
        style.configure("Field.TLabel", font=("Segoe UI", 9, "bold"),
                        background=self.colors["surface"], foreground=self.colors["body"])
        style.configure("PitchValue.TLabel", font=("Segoe UI Semibold", 12),
                        background=self.colors["surface"], foreground=self.colors["accent"])
        style.configure("StatusTitle.TLabel", font=("Segoe UI", 10, "bold"),
                        background=self.colors["surface"], foreground=self.colors["text"])
        style.configure("StatusText.TLabel", font=("Segoe UI", 9),
                        background=self.colors["surface"], foreground=self.colors["body"])
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(14, 10),
                        focuscolor=self.colors["accent"])
        style.configure("Primary.TButton", background="#7657E8", foreground="#FFFFFF")
        style.map("Primary.TButton",
                  background=[("active", self.colors["accent_hover"]), ("disabled", "#334158")],
                  foreground=[("disabled", "#AAB3C3")])
        style.configure("Secondary.TButton", background=self.colors["surface_raised"],
                        foreground=self.colors["text"])
        style.map("Secondary.TButton", background=[("active", "#263750")])
        style.configure("TCombobox", fieldbackground="#F5F7FB", foreground="#101827",
                        padding=9, arrowsize=14, bordercolor=self.colors["border"])
        style.map("TCombobox",
                  fieldbackground=[("readonly", "#F5F7FB"), ("disabled", "#DCE2EB")],
                  foreground=[("readonly", "#101827"), ("disabled", "#657086")])
        style.configure("TScale", background=self.colors["surface"],
                        troughcolor=self.colors["border"], sliderthickness=16)
        style.configure("Voice.Horizontal.TProgressbar", troughcolor=self.colors["border"],
                        background=self.colors["accent"], thickness=10, borderwidth=0)
        style.configure("Card.TCheckbutton", background=self.colors["surface"],
                        foreground=self.colors["text"], font=("Segoe UI", 9))
        style.map("Card.TCheckbutton",
                  background=[("active", self.colors["surface"])],
                  foreground=[("disabled", "#AAB3C3")])

        box = ttk.Frame(self, padding=(24, 18))
        box.pack(fill="both", expand=True)

        header = ttk.Frame(box)
        header.pack(fill="x", pady=(0, 18))
        logo = tk.Canvas(header, width=42, height=42, bg=self.colors["accent"],
                         highlightthickness=0, bd=0)
        logo.pack(side="left", padx=(0, 11))
        for x, height in ((12, 10), (19, 20), (26, 14), (33, 24)):
            logo.create_line(x, 21 - height // 2, x, 21 + height // 2,
                             fill="#FFFFFF", width=2, capstyle=tk.ROUND)
        brand = ttk.Frame(header)
        brand.pack(side="left", fill="y")
        ttk.Label(brand, text="FemaleVocal", style="Brand.TLabel").pack(anchor="w")
        ttk.Label(brand, text="REAL-TIME VOICE STUDIO",
                  font=("Segoe UI", 8, "bold"), foreground=self.colors["muted"],
                  background=self.colors["background"]).pack(anchor="w", pady=(1, 0))
        ttk.Label(header, text="LOCAL PROCESSING", style="Local.TLabel", padding=(11, 6))\
            .pack(side="right", anchor="center")

        ttk.Label(box, text="Live voice changer", style="Title.TLabel").pack(anchor="w")
        ttk.Label(box, text="Set your microphone and output, tune the voice, then go live.",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(4, 15))

        audio_card = ttk.Frame(box, style="Card.TFrame", padding=16)
        audio_card.pack(fill="x", pady=(0, 11))
        audio_head = ttk.Frame(audio_card, style="CardInner.TFrame")
        audio_head.pack(fill="x", pady=(0, 9))
        ttk.Label(audio_head, text="01   AUDIO ROUTING", style="CardTitle.TLabel").pack(side="left")
        self.refresh_button = ttk.Button(audio_head, text="Refresh devices",
                                         style="Secondary.TButton", command=self.refresh)
        self.refresh_button.pack(side="right")
        audio_grid = ttk.Frame(audio_card, style="CardInner.TFrame")
        audio_grid.pack(fill="x")
        audio_grid.columnconfigure(0, weight=1, uniform="device")
        audio_grid.columnconfigure(1, weight=1, uniform="device")
        input_col = ttk.Frame(audio_grid, style="CardInner.TFrame")
        input_col.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        output_col = ttk.Frame(audio_grid, style="CardInner.TFrame")
        output_col.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.input = self.combo(input_col, "MICROPHONE INPUT")
        self.output = self.combo(output_col, "VOICE OUTPUT")

        self.noise_suppression = tk.BooleanVar(value=True)
        self.noise_check = ttk.Checkbutton(
            audio_card, text="Reduce steady background noise",
            variable=self.noise_suppression,
            style="Card.TCheckbutton",
        )
        self.noise_check.pack(anchor="w", pady=(5, 0))
        ttk.Label(audio_card, text="RNNoise runs before voice conversion.",
                  style="CardText.TLabel").pack(anchor="w", padx=(24, 0), pady=(0, 0))

        settings_row = ttk.Frame(box)
        settings_row.pack(fill="x", pady=(0, 11))
        process_card = ttk.Frame(settings_row, style="Card.TFrame", padding=16)
        process_card.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ttk.Label(process_card, text="02   PROCESSING", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(process_card, text="Choose how the voice model runs.",
                  style="CardText.TLabel").pack(anchor="w", pady=(4, 9))
        self.device = self.combo(process_card, "COMPUTE DEVICE")
        self.device["values"] = ("NVIDIA GPU — faster", "CPU — no GPU use")
        self.device.current(0)

        voice_card = ttk.Frame(settings_row, style="Card.TFrame", padding=16)
        voice_card.pack(side="left", fill="both", expand=True, padx=(6, 0))
        ttk.Label(voice_card, text="03   FEMALE VOICE", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(voice_card, text="Public female reference voice",
                  style="PitchValue.TLabel").pack(anchor="w", pady=(8, 4))
        ttk.Label(voice_card, text="Hindi, Marathi and English conversion",
                  style="CardText.TLabel", wraplength=300).pack(anchor="w")

        meter_card = ttk.Frame(box, style="Card.TFrame", padding=(16, 12))
        meter_card.pack(fill="x", pady=(0, 11))
        meter_head = ttk.Frame(meter_card, style="CardInner.TFrame")
        meter_head.pack(fill="x", pady=(0, 7))
        ttk.Label(meter_head, text="MIC INPUT LEVEL", style="CardTitle.TLabel").pack(side="left")
        self.level_text = tk.StringVar(value="Starts when voice conversion is live")
        ttk.Label(meter_head, textvariable=self.level_text, style="CardText.TLabel")\
            .pack(side="right")
        self.level_bar = ttk.Progressbar(meter_card, maximum=100,
                                         style="Voice.Horizontal.TProgressbar")
        self.level_bar.pack(fill="x")

        status_card = ttk.Frame(box, style="Card.TFrame", padding=(16, 12))
        status_card.pack(fill="x", pady=(0, 11))
        status_row = ttk.Frame(status_card, style="CardInner.TFrame")
        status_row.pack(fill="x")
        self.status_dot = tk.Canvas(status_row, width=10, height=10,
                                    bg=self.colors["surface"], highlightthickness=0)
        self.status_dot.pack(side="left", padx=(0, 9), pady=(3, 0))
        self.status_dot_id = self.status_dot.create_oval(1, 1, 9, 9,
                                                         fill=self.colors["muted"], outline="")
        self.status_title = tk.StringVar(value="Ready to start")
        self.status = tk.StringVar(value="Choose your microphone and voice output above.")
        status_copy = ttk.Frame(status_row, style="CardInner.TFrame")
        status_copy.pack(side="left", fill="x", expand=True)
        ttk.Label(status_copy, textvariable=self.status_title,
                  style="StatusTitle.TLabel").pack(anchor="w")
        ttk.Label(status_copy, textvariable=self.status, style="StatusText.TLabel",
                  wraplength=620).pack(anchor="w", pady=(2, 0))

        buttons = ttk.Frame(box)
        buttons.pack(fill="x", pady=(0, 9))
        self.start_button = ttk.Button(buttons, text="Start voice conversion",
                                       style="Primary.TButton",
                                       command=self.start)
        self.start_button.pack(side="left", fill="x", expand=True)
        self.stop_button = ttk.Button(buttons, text="Stop voice",
                                      style="Secondary.TButton",
                                      command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=(8, 0))
        ttk.Label(box, text="CALL SETUP   App output: CABLE Input     •     WhatsApp mic: CABLE Output",
                  font=("Segoe UI", 9, "bold"), foreground=self.colors["body"],
                  background=self.colors["background"], wraplength=760).pack(anchor="w")
        ttk.Label(box, text="Low-latency conversion. First launch downloads model components once; delay depends on your device.",
                  font=("Segoe UI", 9), foreground=self.colors["muted"],
                  background=self.colors["background"]).pack(anchor="w", pady=(3, 0))

        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.worker = None
        self.closing = False
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh()
        self.after(150, self.poll)

    def combo(self, parent, label):
        ttk.Label(parent, text=label, style="Field.TLabel").pack(anchor="w", pady=(0, 3))
        widget = ttk.Combobox(parent, state="readonly", takefocus=True)
        widget.pack(fill="x")
        return widget

    def set_status(self, title, detail, tone="muted"):
        self.status_title.set(title)
        self.status.set(detail)
        color = self.colors.get(tone, self.colors["muted"])
        self.status_dot.itemconfigure(self.status_dot_id, fill=color)

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
                else:
                    widget.set("No compatible device found")
            if not self.inputs or not self.outputs:
                missing = []
                if not self.inputs:
                    missing.append("microphone input")
                if not self.outputs:
                    missing.append("voice output")
                self.set_status("Audio device needed", "No " + " or ".join(missing) + " was found.", "amber")
            elif self.status_title.get() == "Audio device needed":
                self.set_status("Ready to start", "Choose your microphone and voice output above.")
        except Exception as exc:
            self.set_status("Could not list audio devices", str(exc), "red")

    def start(self):
        if self.worker and self.worker.is_alive():
            return
        if self.input.current() < 0 or self.output.current() < 0:
            self.set_status("Choose audio devices", "Select a microphone input and a voice output first.", "amber")
            messagebox.showerror("Choose devices", "Select a microphone and an output device.")
            return
        options = (self.inputs[self.input.current()][0], self.outputs[self.output.current()][0],
                   "cuda" if self.device.current() == 0 else "cpu",
                   self.noise_suppression.get())
        self.cancel.clear()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.refresh_button.configure(state="disabled")
        for widget in (self.input, self.output, self.device, self.noise_check):
            widget.configure(state="disabled")
        self.set_status("Loading voice model", "This can take a few seconds. Stop is available while it loads.", "amber")
        self.worker = threading.Thread(target=self.run_audio, args=options, daemon=True)
        self.worker.start()

    def run_audio(self, input_id, output_id, device, suppress_noise=True):
        engine = None
        suppressor = None
        try:
            import sounddevice as sd
            from types import SimpleNamespace
            from realtime_vc_engine import RealtimeVCEngine

            checkpoint = ROOT / "assets" / "weights" / "indic-female.pth"
            config = ROOT / "seedvc_backend" / "config_dit_mel_seed_uvit_xlsr_tiny.yml"
            reference = ROOT / "assets" / "reference" / "female-reference.wav"
            missing = [str(path) for path in (checkpoint, config, reference) if not path.is_file()]
            if missing:
                raise FileNotFoundError("Required voice files are missing:\n" + "\n".join(missing))

            if suppress_noise:
                from noise_suppression import RNNoiseSuppressor
                suppressor = RNNoiseSuppressor()

            args = SimpleNamespace(
                gpu="cpu" if device == "cpu" else "0",
                fp16=(device == "cuda"),
                checkpoint_path=str(checkpoint),
                config_path=str(config),
            )
            engine = RealtimeVCEngine(args)
            if self.cancel.is_set():
                return

            devices = sd.query_devices()
            hosts = sd.query_hostapis()
            input_info = devices[input_id]
            output_info = devices[output_id]
            hostapi = hosts[input_info["hostapi"]]["name"]
            if hosts[output_info["hostapi"]]["name"] != hostapi:
                matching = [
                    (i, d) for i, d in enumerate(devices)
                    if d["name"] == output_info["name"]
                    and d["max_output_channels"] > 0
                    and hosts[d["hostapi"]]["name"] == hostapi
                ]
                if not matching:
                    raise RuntimeError("Choose an output listed under the same audio system as your microphone.")
                output_id, output_info = matching[0]

            engine.input_suppressor = suppressor
            engine.set_config(
                reference_audio_path=str(reference),
                sg_hostapi=hostapi,
                sg_input_device=input_info["name"],
                sg_output_device=output_info["name"],
                sr_type="sr_model",
                block_time=0.30,
                crossfade_time=0.04,
                extra_time_ce=2.5,
                extra_time=0.5,
                extra_time_right=0.02,
                diffusion_steps=6,
                inference_cfg_rate=0.7,
                max_prompt_length=3.0,
            )

            last_report = [0.0]
            def report(infer_time, delay_time, measured_delay):
                now = time.monotonic()
                if now - last_report[0] < 0.7:
                    return
                last_report[0] = now
                latency_ms = max(delay_time, measured_delay) * 1000
                self.events.put(("status", f"Live • {infer_time * 1000:.0f} ms processing / {latency_ms:.0f} ms estimated delay"))

            engine.on_perf_update = report
            engine.start_stream()
            self.events.put(("status", "Live • female voice conversion is running."))

            while not self.cancel.wait(0.1):
                pass
        except Exception as exc:
            logging.exception("Voice conversion failed")
            self.events.put(("error", str(exc)))
        finally:
            if engine is not None:
                try:
                    engine.stop_stream()
                except Exception:
                    logging.exception("Could not stop Seed-VC stream cleanly")
                if engine.device.type == "cuda":
                    try:
                        import torch
                        torch.cuda.empty_cache()
                    except Exception:
                        pass
                del engine
            if suppressor is not None:
                suppressor.close()
            self.events.put(("done", None))

    def stop(self):
        self.cancel.set()
        self.stop_button.configure(state="disabled")
        self.set_status("Stopping voice", "Waiting for the current audio block to finish.", "amber")

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
                    if value.startswith("Live"):
                        self.set_status("Voice is live", value.replace("Live • ", ""), "green")
                    else:
                        self.set_status("Audio may stutter", value, "amber")
                elif kind == "level":
                    db = 20 * math.log10(max(float(value), 1e-6))
                    level = max(0, min(100, (db + 60) * (100 / 60)))
                    self.level_bar.configure(value=level)
                    self.level_text.set("Speak to check your mic" if level < 3 else "Mic signal detected")
                elif kind == "error":
                    self.set_status("Could not start voice", str(value), "red")
                    if not self.closing:
                        messagebox.showerror("Voice changer stopped", value + f"\n\nLog: {LOGDIR}")
                elif kind == "done":
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    self.refresh_button.configure(state="normal")
                    for widget in (self.input, self.output, self.device):
                        widget.configure(state="readonly")
                    self.noise_check.configure(state="normal")
                    self.level_bar.configure(value=0)
                    self.level_text.set("Starts when voice conversion is live")
                    if self.cancel.is_set():
                        self.set_status("Voice stopped", "Microphone and voice engine have been released.")
                    elif self.status_title.get() != "Could not start voice":
                        self.set_status("Voice stopped", "Ready when you are.")
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

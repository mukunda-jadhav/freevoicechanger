"""FreeVoice: original, local audio effects and soundboard. GPL-3.0-or-later."""
from __future__ import annotations

import json
import os
import math
import queue
import threading
import ctypes
from ctypes import wintypes
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import resample_poly
from pedalboard import Pedalboard, Gain, Reverb, Distortion, Chorus, Delay, HighpassFilter, LowpassFilter

RATE = 48000
BLOCK = 1024
DEFAULT = dict(pitch=0., gain=0., reverb=0., distortion=0., chorus=0., echo=0., robot=0., radio=0.)
PRESETS = {
    'Natural': DEFAULT,
    'Feminine / higher (DSP)': dict(DEFAULT, pitch=4., gain=-2.),
    'Bright / higher (DSP)': dict(DEFAULT, pitch=6., gain=-3.),
    'Deep voice': dict(DEFAULT, pitch=-5.),
    'Robot': dict(DEFAULT, robot=1., distortion=8., gain=-6.),
    'Radio': dict(DEFAULT, radio=1., distortion=5., gain=-4.),
    'Echo': dict(DEFAULT, echo=.35),
    'Space choir': dict(DEFAULT, pitch=3., chorus=.4, reverb=.25, gain=-3.),
}
LIMITS = dict(pitch=(-12, 12), gain=(-24, 12), reverb=(0, .8), distortion=(0, 30), chorus=(0, 1), echo=(0, .7), robot=(0, 1), radio=(0, 1))
DATA_DIR = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'FreeVoice'
LIBRARY = DATA_DIR / 'soundboard.json'


class GlobalHotkeys:
    def __init__(self):
        self.events = queue.SimpleQueue()
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        user32 = ctypes.windll.user32
        keys = [0x70+i for i in range(8)] + [ord('M'), ord('B'), ord('S')]
        registered = []
        unavailable = []
        try:
            for index, key in enumerate(keys):
                if user32.RegisterHotKey(None, index+1, 0x4003, key):
                    registered.append(index+1)
                else:
                    unavailable.append(f'Ctrl+Alt+{("F"+str(index+1)) if index<8 else chr(key)}')
            if unavailable:
                self.events.put(('error', 'Global shortcuts unavailable (occupied or blocked by Windows):\n'+', '.join(unavailable)))
            message = wintypes.MSG()
            while not self.stop_event.wait(.02):
                while user32.PeekMessageW(ctypes.byref(message), None, 0, 0, 1):
                    if message.message == 0x0312:
                        self.events.put(('key', int(message.wParam)-1))
        finally:
            for identifier in registered:
                user32.UnregisterHotKey(None, identifier)

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()


class LivePitch:
    """Two crossfaded fractional delay taps; bounded 43 ms delay window."""
    def __init__(self, semitones):
        self.ratio = 2**(semitones/12)
        self.window = 2048
        self.history = np.zeros(self.window+4, np.float32)
        self.phase = 0.

    def process(self, audio):
        if self.ratio == 1:
            return audio
        extended = np.concatenate((self.history, audio))
        phase = (self.phase + np.arange(len(audio))*(1-self.ratio)/self.window) % 1
        self.phase = (self.phase + len(audio)*(1-self.ratio)/self.window) % 1
        positions = len(self.history) + np.arange(len(audio))
        weight = np.sin(np.pi*phase)**2
        result = np.zeros(len(audio), np.float32)
        for offset, gain in [(0, weight), (.5, 1-weight)]:
            read = positions - ((phase+offset)%1*self.window+2)
            lower = np.floor(read).astype(np.int64)
            frac = read-lower
            result += (extended[lower]*(1-frac)+extended[lower+1]*frac)*gain
        self.history = extended[-len(self.history):].copy()
        return result


def validated(values):
    if not isinstance(values, dict):
        raise ValueError('Preset must be a JSON object.')
    result = dict(DEFAULT)
    for key, (low, high) in LIMITS.items():
        value = float(values.get(key, DEFAULT[key]))
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'{key} must be between {low} and {high}.')
        result[key] = value
    return result


class Effects:
    def __init__(self, values):
        self.values = validated(values)
        p = self.values
        plugins = []
        self.pitch = LivePitch(p['pitch'])
        if p['radio']:
            plugins.extend([HighpassFilter(cutoff_frequency_hz=350), LowpassFilter(cutoff_frequency_hz=3200)])
        if p['distortion']:
            plugins.append(Distortion(drive_db=p['distortion']))
        if p['chorus']:
            plugins.append(Chorus(mix=p['chorus']))
        if p['echo']:
            plugins.append(Delay(delay_seconds=.22, feedback=.25, mix=p['echo']))
        if p['reverb']:
            plugins.append(Reverb(room_size=.4, wet_level=p['reverb'], dry_level=1-p['reverb']))
        plugins.append(Gain(gain_db=p['gain']))
        self.board = Pedalboard(plugins)
        self.phase = 0

    def process(self, audio):
        audio = np.asarray(audio, dtype=np.float32).reshape(-1)
        audio = self.pitch.process(audio)
        if self.values['robot']:
            phase = np.arange(len(audio)) + self.phase
            audio = audio * np.sin(phase * (2*np.pi*75/RATE))
            self.phase += len(audio)
        # Queue the actual returned samples without discarding any plugin tail.
        result = self.board(audio, RATE, buffer_size=BLOCK, reset=False)
        return np.clip(np.asarray(result).reshape(-1), -.98, .98).astype(np.float32)


class Recorder:
    def __init__(self, path, errors):
        self.queue = queue.Queue(maxsize=256)
        self.errors = errors
        self.file = sf.SoundFile(path, 'w', samplerate=RATE, channels=1, subtype='PCM_16')
        self.failed = False
        self.thread = threading.Thread(target=self._write, daemon=True)
        self.thread.start()

    def put(self, samples):
        if self.failed:
            return
        try:
            self.queue.put_nowait(samples.copy())
        except queue.Full:
            self.failed = True
            self.errors.put('Recording stopped receiving audio: disk writer is too slow. Stop recording to finalize the file.')

    def _write(self):
        try:
            while True:
                data = self.queue.get()
                if data is None:
                    break
                self.file.write(data)
        except Exception as exc:
            self.failed = True
            self.errors.put(f'Recording error: {exc}')
        finally:
            self.file.close()

    def close(self):
        while self.thread.is_alive():
            try:
                self.queue.put(None, timeout=.1)
                break
            except queue.Full:
                continue
        self.thread.join()


class Engine:
    def __init__(self):
        self.stream = None
        self.errors = queue.SimpleQueue()
        self.parameters = dict(DEFAULT)
        self.muted = False
        self.bypass = False
        self.peak = 0.
        self.xruns = 0
        self.record_lock = threading.Lock()
        self.recorder = None
        self.sound_lock = threading.Lock()
        self.sound = None
        self.sound_position = 0

    def start(self, input_device, output_device):
        self.stop()
        self.inbox = queue.Queue(maxsize=12)
        self.outbox = queue.Queue(maxsize=12)
        self.running = threading.Event()
        self.running.set()
        self.pending = np.empty(0, np.float32)
        self.xruns = 0
        try:
            self.stream = sd.Stream(device=(input_device, output_device), samplerate=RATE,
                                    blocksize=BLOCK, channels=(1, 1), dtype='float32',
                                    latency='low', callback=self._callback)
            self.worker = threading.Thread(target=self._process, daemon=True)
            self.worker.start()
            self.stream.start()
        except Exception:
            self.stop()
            raise

    def _callback(self, indata, outdata, frames, timing, status):
        if status:
            self.xruns += 1
        try:
            self.inbox.put_nowait(indata[:, 0].copy())
        except queue.Full:
            self.xruns += 1
        # One consumer owns pending; output arrays can have any size.
        outdata.fill(0)
        offset = 0
        while offset < frames:
            if not len(self.pending):
                try:
                    self.pending = self.outbox.get_nowait()
                except queue.Empty:
                    break
            count = min(frames-offset, len(self.pending))
            outdata[offset:offset+count, 0] = self.pending[:count]
            self.pending = self.pending[count:]
            offset += count

    def _process(self):
        last = None
        effects = None
        while self.running.is_set():
            try:
                audio = self.inbox.get(timeout=.1)
            except queue.Empty:
                continue
            try:
                p = self.parameters.copy()
                signature = (tuple(p.items()), self.bypass)
                if signature != last:
                    effects = Effects(DEFAULT if self.bypass else p)
                    last = signature
                audio = effects.process(audio)
                if self.muted:
                    audio.fill(0)
                with self.sound_lock:
                    if self.sound is not None and len(audio):
                        count = min(len(audio), len(self.sound)-self.sound_position)
                        audio[:count] += self.sound[self.sound_position:self.sound_position+count] * .65
                        self.sound_position += count
                        if self.sound_position >= len(self.sound):
                            self.sound = None
                audio = np.clip(audio, -.98, .98)
                self.peak = float(np.max(np.abs(audio))) if len(audio) else 0.
                if len(audio):
                    with self.record_lock:
                        if self.recorder:
                            self.recorder.put(audio)
                    try:
                        self.outbox.put_nowait(audio)
                    except queue.Full:
                        self.xruns += 1
            except Exception as exc:
                self.errors.put(f'Audio processing stopped: {exc}')
                self.running.clear()

    def play(self, samples):
        with self.sound_lock:
            self.sound = samples
            self.sound_position = 0

    def stop_sound(self):
        with self.sound_lock:
            self.sound = None

    def set_recording(self, path=None):
        with self.record_lock:
            old = self.recorder
            self.recorder = None
        if old:
            old.close()
        if path:
            new = Recorder(path, self.errors)
            with self.record_lock:
                self.recorder = new

    def stop(self):
        if hasattr(self, 'running'):
            self.running.clear()
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        if hasattr(self, 'worker'):
            self.worker.join()
        self.set_recording()
        self.stop_sound()
        self.peak = 0.


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('FreeVoice — Local voice studio')
        self.geometry('920x790')
        self.minsize(800, 730)
        self.configure(bg='#111827')
        self.engine = Engine()
        self.hotkeys = GlobalHotkeys()
        self.sounds = []
        self.change_timer = None
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 11), background='#111827', foreground='#F8FAFC')
        style.configure('TButton', padding=(14, 9), background='#334155')
        style.map('TButton', background=[('active', '#475569'), ('disabled', '#1E293B')])
        style.configure('TCombobox', fieldbackground='#F8FAFC', foreground='#111827', padding=5)
        style.configure('TNotebook.Tab', padding=(18, 10), background='#334155')
        style.map('TNotebook.Tab', background=[('selected', '#4338CA')])
        style.configure('TLabelframe.Label', foreground='#A5B4FC')
        style.configure('Title.TLabel', font=('Segoe UI', 25, 'bold'))
        style.configure('Muted.TLabel', foreground='#CBD5E1')
        body = ttk.Frame(self, padding=22)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='FreeVoice', style='Title.TLabel').pack(anchor='w')
        ttk.Label(body, text='Local effects and soundboard. No subscriptions.', style='Muted.TLabel').pack(anchor='w', pady=(3, 16))
        routing = ttk.LabelFrame(body, text='Audio routing', padding=12)
        routing.pack(fill='x')
        routing.columnconfigure(1, weight=1)
        ttk.Label(routing, text='Microphone').grid(row=0, column=0, sticky='w', padx=(0, 12))
        ttk.Label(routing, text='Output').grid(row=1, column=0, sticky='w', padx=(0, 12))
        self.input = ttk.Combobox(routing, state='readonly')
        self.output = ttk.Combobox(routing, state='readonly')
        self.input.grid(row=0, column=1, sticky='ew', pady=4)
        self.output.grid(row=1, column=1, sticky='ew', pady=4)
        self.refresh_button = ttk.Button(routing, text='Refresh', command=self.devices)
        self.refresh_button.grid(row=0, column=2, rowspan=2, padx=(12, 0))
        ttk.Label(routing, text='Use headphones for listening. For chat, select a virtual cable output.', style='Muted.TLabel').grid(row=2, column=0, columnspan=3, sticky='w', pady=(8, 0))
        controls = ttk.Frame(body)
        controls.pack(fill='x', pady=14)
        self.start_button = ttk.Button(controls, text='Start microphone', command=self.toggle)
        self.start_button.pack(side='left')
        self.mute = tk.BooleanVar()
        self.bypass = tk.BooleanVar()
        ttk.Checkbutton(controls, text='Mute mic (Ctrl+M)', variable=self.mute, command=self.options).pack(side='left', padx=18)
        ttk.Checkbutton(controls, text='Bypass effects (Ctrl+B)', variable=self.bypass, command=self.options).pack(side='left')
        tabs = ttk.Notebook(body)
        tabs.pack(fill='both', expand=True)
        lab = ttk.Frame(tabs, padding=16)
        board = ttk.Frame(tabs, padding=16)
        tabs.add(lab, text='Voice Lab')
        tabs.add(board, text='Soundboard')
        top = ttk.Frame(lab)
        top.pack(fill='x')
        self.preset = ttk.Combobox(top, values=list(PRESETS), state='readonly', width=27)
        self.preset.current(1)
        self.preset.pack(side='left')
        self.preset.bind('<<ComboboxSelected>>', lambda e: self.apply(PRESETS[self.preset.get()]))
        ttk.Button(top, text='Save preset', command=self.save_preset).pack(side='right')
        ttk.Button(top, text='Load preset', command=self.load_preset).pack(side='right', padx=8)
        ttk.Label(lab, text='Higher voices use pitch shifting, not an AI female voice model.', style='Muted.TLabel').pack(anchor='w', pady=(10, 12))
        sliders = ttk.Frame(lab)
        sliders.pack(fill='x')
        sliders.columnconfigure(1, weight=1)
        self.values = {}
        for row, (key, bounds) in enumerate(LIMITS.items()):
            label = {'pitch':'Pitch (semitones)', 'gain':'Gain (dB)', 'robot':'Robot modulation', 'radio':'Radio filter'}.get(key, key.title())
            ttk.Label(sliders, text=label).grid(row=row, column=0, sticky='w', padx=(0, 18), pady=5)
            variable = tk.DoubleVar(value=0)
            self.values[key] = variable
            ttk.Scale(sliders, from_=bounds[0], to=bounds[1], variable=variable, command=self.changed).grid(row=row, column=1, sticky='ew', pady=5)
            number = ttk.Label(sliders, width=7, anchor='e')
            number.grid(row=row, column=2, padx=(12, 0))
            variable.trace_add('write', lambda *args, v=variable, n=number: n.configure(text=f'{v.get():.2f}'))
        ttk.Label(lab, text='Changes apply when sliders pause. Robot / radio are on above zero.', style='Muted.TLabel').pack(anchor='w', pady=(12, 0))
        ttk.Label(board, text='Add clips and play them into the same output as your voice.').pack(anchor='w')
        ttk.Label(board, text='F1–F8 play clips in this app. Escape stops. Global keys use Ctrl+Alt.', style='Muted.TLabel').pack(anchor='w', pady=(5, 12))
        self.global_keys = tk.BooleanVar()
        ttk.Checkbutton(board, text='Enable global shortcuts: Ctrl+Alt+F1–F8 / M mute / B bypass / S stop', variable=self.global_keys, command=self.toggle_global).pack(anchor='w', pady=(0, 10))
        self.clip_list = tk.Listbox(board, bg='#1E293B', fg='#F8FAFC', selectbackground='#4338CA', font=('Segoe UI', 12), height=10, exportselection=False)
        self.clip_list.pack(fill='both', expand=True)
        self.clip_list.bind('<Double-Button-1>', lambda e: self.play_selected())
        buttons = ttk.Frame(board)
        buttons.pack(fill='x', pady=12)
        for text, command in [('Add clips', self.add_clips), ('Play selected', self.play_selected), ('Stop clip', self.engine.stop_sound), ('Remove', self.remove_clip)]:
            ttk.Button(buttons, text=text, command=command).pack(side='left', padx=(0, 8))
        footer = ttk.Frame(body)
        footer.pack(fill='x', pady=(15, 0))
        self.record_button = ttk.Button(footer, text='Record WAV', command=self.record)
        self.record_button.pack(side='right')
        self.status = ttk.Label(footer, text='Stopped · microphone is off', style='Muted.TLabel')
        self.status.pack(side='left')
        self.meter = ttk.Progressbar(body, maximum=1.)
        self.meter.pack(fill='x', pady=(10, 0))
        self.bind('<Control-m>', lambda e: self.key_option(self.mute))
        self.bind('<Control-b>', lambda e: self.key_option(self.bypass))
        self.bind('<Escape>', lambda e: self.engine.stop_sound())
        for i in range(8):
            self.bind(f'<F{i+1}>', lambda e, index=i: self.play_clip(index))
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.apply(PRESETS[self.preset.get()])
        self.devices()
        self.restore_library()
        self.after(150, self.poll)

    def devices(self):
        try:
            devices = sd.query_devices()
            hosts = sd.query_hostapis()
            self.inputs = [(i, f"{d['name']} [{hosts[d['hostapi']]['name']}]") for i, d in enumerate(devices) if d['max_input_channels'] > 0]
            self.outputs = [(i, f"{d['name']} [{hosts[d['hostapi']]['name']}]") for i, d in enumerate(devices) if d['max_output_channels'] > 0]
            for combo, options, default in [(self.input, self.inputs, sd.default.device[0]), (self.output, self.outputs, sd.default.device[1])]:
                combo['values'] = [label for _, label in options]
                if options:
                    combo.current(next((j for j, (i, _) in enumerate(options) if i == default), 0))
        except Exception as exc:
            messagebox.showerror('Audio devices', str(exc))

    def toggle_global(self):
        if self.global_keys.get():
            self.hotkeys.start()
        else:
            self.hotkeys.stop()

    def restore_library(self):
        if LIBRARY.exists():
            try:
                paths = json.loads(LIBRARY.read_text(encoding='utf-8'))
                if not isinstance(paths, list):
                    raise ValueError('Invalid library')
                self.import_clips(paths)
            except Exception as exc:
                messagebox.showwarning('Soundboard library', str(exc))

    def save_library(self):
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            LIBRARY.write_text(json.dumps([item[2] for item in self.sounds], indent=2), encoding='utf-8')
        except OSError as exc:
            messagebox.showwarning('Soundboard library', str(exc))

    def options(self):
        self.engine.muted = self.mute.get()
        self.engine.bypass = self.bypass.get()

    def key_option(self, variable):
        variable.set(not variable.get())
        self.options()

    def changed(self, *_):
        if self.change_timer:
            self.after_cancel(self.change_timer)
        self.change_timer = self.after(250, self.commit)

    def commit(self):
        self.change_timer = None
        self.engine.parameters = validated({key: v.get() for key, v in self.values.items()})

    def apply(self, parameters):
        for key, value in validated(parameters).items():
            self.values[key].set(value)
        self.commit()

    def toggle(self):
        if self.engine.stream:
            self.engine.stop()
            self.stopped()
            return
        try:
            if self.input.current() < 0 or self.output.current() < 0:
                raise ValueError('Choose an input and an output device.')
            self.commit()
            self.engine.start(self.inputs[self.input.current()][0], self.outputs[self.output.current()][0])
            self.start_button.configure(text='Stop microphone')
            self.input.configure(state='disabled')
            self.output.configure(state='disabled')
            self.refresh_button.configure(state='disabled')
        except Exception as exc:
            messagebox.showerror('Could not start audio', f'{exc}\n\nTry input and output with the same host API (e.g. WASAPI), both supporting 48 kHz.')

    def stopped(self):
        self.start_button.configure(text='Start microphone')
        self.record_button.configure(text='Record WAV')
        self.input.configure(state='readonly')
        self.output.configure(state='readonly')
        self.refresh_button.configure(state='normal')

    def record(self):
        if self.engine.recorder:
            self.engine.set_recording()
            self.record_button.configure(text='Record WAV')
            return
        if not self.engine.stream:
            messagebox.showinfo('Start audio', 'Start the microphone before recording.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.wav', filetypes=[('WAV audio', '*.wav')])
        if path:
            try:
                self.engine.set_recording(path)
                self.record_button.configure(text='Stop recording')
            except Exception as exc:
                messagebox.showerror('Recording', str(exc))

    def save_preset(self):
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('FreeVoice preset', '*.json')])
        if path:
            try:
                self.commit()
                Path(path).write_text(json.dumps(self.engine.parameters, indent=2), encoding='utf-8')
            except Exception as exc:
                messagebox.showerror('Save preset', str(exc))

    def load_preset(self):
        path = filedialog.askopenfilename(filetypes=[('FreeVoice preset', '*.json')])
        if path:
            try:
                self.apply(json.loads(Path(path).read_text(encoding='utf-8')))
                self.preset.set('Custom preset')
            except Exception as exc:
                messagebox.showerror('Load preset', str(exc))

    def add_clips(self):
        self.import_clips(filedialog.askopenfilenames(filetypes=[('Audio', '*.wav *.mp3 *.flac *.ogg'), ('All files', '*.*')]))
        self.save_library()

    def import_clips(self, paths):
        for path in paths:
            try:
                info = sf.info(path)
                if info.duration > 120:
                    raise ValueError('Use a clip of 120 seconds or less.')
                if sum(item[1].nbytes for item in self.sounds) + info.duration*RATE*4 > 256*1024*1024:
                    raise ValueError('Soundboard memory budget is 256 MB. Remove clips to make room.')
                data, rate = sf.read(path, dtype='float32', always_2d=True)
                mono = data.mean(axis=1)
                divisor = math.gcd(RATE, rate)
                samples = resample_poly(mono, RATE//divisor, rate//divisor).astype(np.float32)
                self.sounds.append((Path(path).name, samples, str(Path(path).resolve())))
                self.refresh_clips()
            except Exception as exc:
                messagebox.showerror('Import clip', f'{Path(path).name}: {exc}')

    def refresh_clips(self):
        self.clip_list.delete(0, 'end')
        for i, (name, data, path) in enumerate(self.sounds):
            hotkey = f'F{i+1}' if i < 8 else '—'
            self.clip_list.insert('end', f'{hotkey:4}  {name}  ·  {len(data)/RATE:.1f}s')

    def play_clip(self, index):
        if not self.engine.stream:
            self.status.configure(text='Start the microphone to play clips.')
        elif index < len(self.sounds):
            self.engine.play(self.sounds[index][1])

    def play_selected(self):
        selected = self.clip_list.curselection()
        if selected:
            self.play_clip(selected[0])

    def remove_clip(self):
        selected = self.clip_list.curselection()
        if selected:
            self.sounds.pop(selected[0])
            self.refresh_clips()
            self.save_library()

    def poll(self):
        while not self.hotkeys.events.empty():
            kind, value = self.hotkeys.events.get_nowait()
            if kind == 'error':
                messagebox.showwarning('Global shortcut', value)
            elif value < 8:
                self.play_clip(value)
            elif value == 8:
                self.key_option(self.mute)
            elif value == 9:
                self.key_option(self.bypass)
            else:
                self.engine.stop_sound()
        self.meter['value'] = self.engine.peak
        if self.engine.stream:
            recording = ' · RECORDING' if self.engine.recorder else ''
            self.status.configure(text=f'Live · 48 kHz · audio overruns: {self.engine.xruns}{recording}')
        else:
            self.status.configure(text='Stopped · microphone is off')
        try:
            error = self.engine.errors.get_nowait()
            self.engine.stop()
            self.stopped()
            messagebox.showerror('Audio stopped', error)
        except queue.Empty:
            pass
        self.after(150, self.poll)

    def close(self):
        self.hotkeys.stop()
        self.engine.stop()
        self.destroy()


if __name__ == '__main__':
    App().mainloop()

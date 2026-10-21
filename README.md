# FreeVoice

Windows desktop voice changer with one ready-made female RVC voice (VCTK p231).
The current implementation is in **desktop/**. Root-level DSP files are an older prototype.

The app offers microphone/output selection, pitch control, CPU or NVIDIA GPU processing,
and Start/Stop. It performs local streaming conversion without training or an account.
Calls require a separately installed virtual audio cable. Audio blocks are 500 ms;
additional model and device buffering produces noticeable delay.

## Status

A short example was rendered with the ready-made voice. Live microphone routing and
the executable on a clean machine still need user validation. This is a private
development preview, not a promise of Voicemod-level quality.

## Build / download

See [desktop/BUILD.md](desktop/BUILD.md). The manual **Actions → FreeVoice ready-made
voice desktop build** workflow produces a Windows artifact containing FreeVoice.exe
and its runtime. Extract the complete artifact before opening FreeVoice.exe.
No Python installation is needed to use the packaged executable.

## Voice and licenses

- Voice: [Nekochu's VCTK p231 model](https://huggingface.co/Nekochu/RVC-VCTK_Voice-sample), model card Apache-2.0.
- Inference: RVC Project (MIT), pinned source revision recorded in prepare_build.py.
- App distribution: GPL-3.0-or-later due to bundled Parselmouth/Praat; component notices apply.

No personal recordings, custom training datasets or custom voice checkpoints are included.
The repository remains private during development.

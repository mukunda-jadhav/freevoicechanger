# FreeVoice

Windows desktop voice changer with **one female voice**. Runs locally, with no training or Python installation needed.

[![Download desktop app for Windows](https://img.shields.io/badge/Download_desktop_app-Windows_x64-7253D6?style=for-the-badge&logo=windows)](https://github.com/mukunda-jadhav/freevoicechanger/releases/tag/desktop-preview)

## Download and install

1. Open the download button above and expand **Assets**.
2. Download **FreeVoice-Setup-Windows-x64.exe** and **every matching .bin file** into the same folder.
3. Run the setup EXE. Open **FreeVoice** from the desktop shortcut.

Keep all installer files together until installation finishes. The data files contain the voice and GPU runtime; they are not source code. The download is several GB. The installer is unsigned.

**Private development preview:** sign in to GitHub with an account that has access to this repository. Downloads are not public while the repository is private.

## Use

- Select your microphone and headphones/output device.
- Choose NVIDIA GPU for faster processing, or CPU (which may not keep up).
- Start at pitch **+12** and adjust to your voice.
- Press **Start**, then **Stop** when finished.

For Discord, games, or calls, install a virtual audio cable separately. Select its playback/input device as FreeVoice's output, then its recording/output device as the microphone in your calling app. Use headphones to avoid feedback.

## Current limitations

This is an early preview. A short audio example has been rendered with the model, but live microphone routing and a clean-machine executable launch still need user validation. Audio blocks are 500 ms, plus model and device buffering; expect noticeable delay. Naturalness depends on the speaker and microphone.

## Source and builds

The current application is in **desktop/**. Root-level DSP files are an older prototype.
See [build instructions](desktop/BUILD.md). The Windows release workflow builds the executable and installer on GitHub and publishes the development preview. The installer includes corresponding app/inference source and license notices.

## Voice and licenses

- One ready-made [VCTK p231 female voice by Nekochu](https://huggingface.co/Nekochu/RVC-VCTK_Voice-sample), model card Apache-2.0.
- Inference: RVC Project (MIT); pinned revision in `desktop/prepare_build.py`.
- App distribution: GPL-3.0-or-later due to bundled Parselmouth/Praat; component notices apply.

No personal recordings, custom training datasets or custom voice checkpoints are included.

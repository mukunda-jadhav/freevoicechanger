# FreeVoice

A free Windows desktop voice-effects app with local processing, eight presets, editable effects, a soundboard, and WAV recording. No account or subscription.

## Download and open

Download `FreeVoice-0.1.0-Windows-x64.zip` from this repository's **Releases** page, extract the entire folder, and double-click **FreeVoice.exe**. Keep the `_internal` folder beside the executable. Python and command-line setup are not required for this portable build. The initial release is unsigned.

Select a microphone and output, put on headphones, select a preset, and click **Start microphone**. Capture only starts when you press that button. Closing the window stops capture and finalizes recording.

## Features

- Eight presets: Natural, Feminine / higher (DSP), Bright / higher (DSP), Deep voice, Robot, Radio, Echo, Space choir.
- Adjustable pitch, gain, reverb, distortion, chorus, delay, robot modulation and radio filtering.
- Save/load JSON presets; persistent soundboard clip paths in `%LOCALAPPDATA%\FreeVoice\soundboard.json`.
- Soundboard clips up to 120 seconds each, within a 256 MB decoded memory budget, one clip at a time.
- Microphone mute, effect bypass, level display, processed mono WAV recording.
- App shortcuts: Ctrl+M mute, Ctrl+B bypass, F1–F8 clips, Escape stop clip.
- Optional global shortcuts: Ctrl+Alt+F1–F8 clips, Ctrl+Alt+M mute, Ctrl+Alt+B bypass, Ctrl+Alt+S stop clip. Other apps may already own these keys.

## Use in calls

A virtual audio cable is required separately. With optional [VB-CABLE](https://vb-audio.com/Cable/), choose **CABLE Input** as FreeVoice output and **CABLE Output** as the microphone in Discord or your game. FreeVoice does not bundle or install a driver.

## Quality and current limits

This is an early DSP prototype. The feminine preset raises pitch; it is **not natural AI male-to-female conversion**. It does not independently adjust formants. Granular pitch shifting can introduce audible modulation. It has no AI model library, cloud generation, voice cloning or complete Voicemod feature parity.

Audio uses 48 kHz mono, 1,024-frame blocks. The pitch delay window is about 43 ms; queues and device buffering add latency. Live device compatibility and perceived quality remain unverified. Output is hard-clipped at ±0.98; reduce gain if it sounds harsh. Preset changes reset effect history. Recording captures the processed mix before device playback.

Prior source checks passed eight synthetic presets, pitch shifting, recording finalization, invalid preset rejection, callback sample delivery and interface construction. Global shortcut registration was rejected in the check environment. The packaged executable has not been tested on a clean Windows machine.

## Build from source (developers only)

On Windows x64 with Python 3.13:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python build.py
```

The `dist` folder contains the portable ZIP, app source ZIP and SHA-256 checksums. GitHub Actions provides the same build on manual dispatch or tags matching `v*`. A tag build publishes a **draft prerelease** for review; publish it from Releases to make downloads public. Keep the tag and `VERSION` in `build.py` aligned.

## License

Original app code: GPL-3.0-or-later; see LICENSE. Dependencies retain their own licenses. Pedalboard notices are included. Binary packages preserve installed third-party license notices and a package inventory. Source is provided in the repository and matching release source ZIP. Dependency source distributions are available from their versioned PyPI project pages and upstream projects; retain their required notices and source availability when redistributing.

This is an independently written app. No Voicemod code, models, extracted resources, account data or branding are distributed.

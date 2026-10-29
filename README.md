# FreeVoice

Windows desktop male-to-female voice changer using one public female reference voice and the IndicVoiceChanger Seed-VC model. It is intended for English, Hindi, and Marathi, and processes microphone audio locally.

## Download

The `femalevocal-indic` branch contains the updated source. The existing `desktop-preview` release is still the earlier build until this branch is merged and its Windows release workflow completes.

After release, the Windows installer will be available here:

[![Download desktop app for Windows](https://img.shields.io/badge/Download_desktop_app-Windows_x64-7253D6?style=for-the-badge&logo=windows)](https://github.com/mukunda-jadhav/freevoicechanger/releases/tag/desktop-preview)

The first run downloads shared model components once (about 1–2 GB); later conversion runs locally. A virtual audio cable is needed to route converted audio into calling apps.

## Run from source

See [desktop/BUILD.md](desktop/BUILD.md). For calls, select the virtual cable as the app output and the cable's recording device as the calling app microphone. Use headphones to avoid feedback.

## Model and reference

- IndicVoiceChanger fine-tuned Seed-VC checkpoint, fetched and SHA-256 verified by `desktop/prepare_build.py`.
- Public female reference sample `s1p1.wav`, with source and attribution in `desktop/REFERENCE-VOICE-SOURCE.txt`.
- The repository does not include private recordings, user-trained voice checkpoints, or downloaded model weights.

See the included license files and notices before redistributing a build.

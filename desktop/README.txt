FreeVoice — ready-made female voice

Open FreeVoice.exe. No Python installation or command entry is needed.
Keep the _internal folder beside the executable.

1. Select your microphone and headphones.
2. Select NVIDIA GPU (faster) or CPU (uses no GPU).
3. Start with pitch +12; adjust between +7 and +12 to suit your voice.
4. Press Start voice changer. Loading may take a while.
5. Press Stop when finished. Closing the window also stops audio.

For Discord, games, or calls:
You need a virtual audio cable installed separately.
Select its playback/Input device as FreeVoice's output. Select the
corresponding recording/Output device as the microphone in the calling app.
This app does not install a virtual audio driver.

Use headphones to avoid feedback. There is noticeable delay: blocks are
500 ms, plus model lookahead and audio-device buffering. CPU performance
may be too slow for uninterrupted speech. The status line reports processing
time and overloads. Naturalness depends on the speaker and microphone.

This version contains one pretrained VCTK p231 female voice. It does not
use your friend's recordings or train models. All conversion runs locally.
No guarantee is made that it matches Voicemod quality.

Logs: %LOCALAPPDATA%\FreeVoice

Credits:
RVC-Project/Retrieval-based-Voice-Conversion-WebUI — MIT (RVC-LICENSE.txt)
Nekochu/RVC-VCTK_Voice-sample, F/p231/rmvpe — Apache-2.0
https://huggingface.co/Nekochu/RVC-VCTK_Voice-sample
Training dataset: CSTR Edinburgh VCTK; attribution retained here.
Shared HuBERT and RMVPE assets:
https://huggingface.co/lj1995/VoiceConversionWebUI
App streaming adapter and UI are modified integrations, not upstream GUIs.
See THIRD-PARTY-NOTICES.txt for redistribution notes.

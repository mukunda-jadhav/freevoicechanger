# Build FreeVoice

Use Windows x64 and Python 3.12. The packaged app does not need Python installed.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install torch==2.7.1+cu118 torchaudio==2.7.1+cu118 --index-url https://download.pytorch.org/whl/cu118
.venv\Scripts\python -m pip install -r requirements-app.txt
.venv\Scripts\python prepare_build.py
.venv\Scripts\python build_desktop.py
```

The result is `dist/FreeVoice/FreeVoice.exe` plus its `_internal` folder.
Ship the whole directory, README, notices and corresponding source together.
Git and curl are needed only to prepare the build.

The ready-made p231 model has been used to render a short sample. Live microphone
routing and a clean-machine executable launch have not yet been verified.
No quality claim is implied by successful packaging.

Do not include personal voice recordings, training logs, or checkpoints in a release.

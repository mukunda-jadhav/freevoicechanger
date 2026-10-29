# Build FemaleVocalIndic

Use Windows x64, Python 3.12, and an NVIDIA driver with CUDA support. The
runtime checkpoint and public reference are in assets. The shared encoder
and vocoder weights download the first time the app starts.

    py -3.12 -m venv .venv
    .venv\Scripts\python -m pip install torch==2.7.1+cu118 torchaudio==2.7.1+cu118 --index-url https://download.pytorch.org/whl/cu118
    .venv\Scripts\python -m pip install -r requirements-app.txt
    .venv\Scripts\python prepare_build.py
    .venv\Scripts\python build_desktop.py
    .venv\Scripts\python package_source.py

The result is dist/FemaleVocalIndic/FemaleVocalIndic.exe plus its _internal
folder. Keep and distribute the complete folder, not the executable alone.

Model components download to %LOCALAPPDATA%\FemaleVocal\models. If you
redistribute the app, include its source archive and license notices and
comply with the included GPL-3.0 license.

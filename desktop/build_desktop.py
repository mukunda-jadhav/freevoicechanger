"""Package the Indic Seed-VC desktop app as a Windows onedir build."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SEED = ROOT / "seedvc_backend" / "seed-vc-realtime"
APP_DIST = ROOT / "dist" / "FemaleVocalIndic"
LEGACY_BUNDLED = ROOT / "dist" / "FemaleVocal" / "_internal"
STAGED_BUNDLE = ROOT / "build" / "runtime-base"
BUNDLED = None
STAGED_EXISTING_APP = False
if APP_DIST.is_dir():
    if STAGED_BUNDLE.exists():
        raise RuntimeError(f"Refusing to reuse existing build staging folder: {STAGED_BUNDLE}")
    STAGED_BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    APP_DIST.rename(STAGED_BUNDLE)
    BUNDLED = STAGED_BUNDLE / "_internal"
    STAGED_EXISTING_APP = True
elif LEGACY_BUNDLED.is_dir():
    BUNDLED = LEGACY_BUNDLED
files = [
    ("assets/weights/indic-female.pth", "assets/weights"),
    ("assets/reference/female-reference.wav", "assets/reference"),
    ("seedvc_backend/config_dit_mel_seed_uvit_xlsr_tiny.yml", "seedvc_backend"),
    ("seedvc_backend/seed-vc-realtime/configs/hifigan.yml", "configs"),
    ("rnnoise.dll", "."),
    ("README.txt", "."),
    ("MODEL-LICENSE.txt", "."),
    ("REFERENCE-VOICE-SOURCE.txt", "."),
    ("SEEDVC-LICENSE.txt", "."),
    ("THIRD-PARTY-NOTICES.txt", "."),
    ("PYRNNOISE-LICENSE.txt", "."),
    ("RNNOISE-LICENSE.txt", "."),
    ("LICENSE", "."),
]
args = [
    sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
    "--windowed", "--name", "FemaleVocalIndic",
    "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build" / "indic"),
    "--specpath", str(ROOT), "--paths", str(SEED),
    "--collect-all", "transformers", "--collect-all", "torchaudio",
    "--collect-all", "librosa", "--collect-all", "sounddevice",
    "--collect-all", "huggingface_hub",
    "--collect-submodules", "audio_modules",
    "--copy-metadata", "transformers", "--copy-metadata", "huggingface-hub",
    "--copy-metadata", "sounddevice",
    "--collect-submodules", "torchgen", "--collect-submodules", "torio",
    "--exclude-module", "funasr", "--exclude-module", "modelscope",
    "--exclude-module", "tensorboard", "--exclude-module", "matplotlib",
    "--exclude-module", "IPython", "--exclude-module", "pytest",
]
env = os.environ.copy()
BUILD_SITE = Path(sys.prefix) / "Lib" / "site-packages"
if BUNDLED is not None and BUNDLED.is_dir():
    args += ["--paths", str(BUNDLED)]
previous = env.get("PYTHONPATH", "")
search_paths = [str(BUILD_SITE)]
if BUNDLED is not None and BUNDLED.is_dir():
    search_paths.append(str(BUNDLED))
if previous:
    search_paths.append(previous)
env["PYTHONPATH"] = os.pathsep.join(search_paths)
for source, destination in files:
    args += ["--add-data", f"{ROOT / source};{destination}"]
args.append(str(ROOT / "freevoice.py"))
try:
    subprocess.run(args, cwd=ROOT, check=True, env=env)
except Exception:
    if STAGED_EXISTING_APP:
        if APP_DIST.exists():
            shutil.rmtree(APP_DIST)
        STAGED_BUNDLE.rename(APP_DIST)
    raise
else:
    if STAGED_EXISTING_APP:
        shutil.rmtree(STAGED_BUNDLE)




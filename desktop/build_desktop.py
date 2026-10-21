from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parent
args = [
    sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--windowed",
    "--name", "FreeVoice", "--distpath", str(ROOT / "dist"),
    "--workpath", str(ROOT / "build"), "--specpath", str(ROOT),
    "--collect-all", "transformers", "--collect-all", "torchaudio",
    "--collect-all", "librosa", "--collect-all", "sounddevice",
    "--recursive-copy-metadata", "transformers",
    "--copy-metadata", "praat-parselmouth", "--copy-metadata", "sounddevice",
    "--exclude-module", "tensorboard", "--exclude-module", "matplotlib",
    "--exclude-module", "IPython", "--exclude-module", "pytest",
]
for name in ("assets", "i18n", "configs", "RVC-LICENSE.txt",
             "THIRD-PARTY-NOTICES.txt", "MODEL-LICENSE.txt", "LICENSE"):
    destination = name if (ROOT / name).is_dir() else "."
    args += ["--add-data", f"{ROOT / name};{destination}"]
args.append(str(ROOT / "freevoice.py"))
subprocess.run(args, cwd=ROOT, check=True)

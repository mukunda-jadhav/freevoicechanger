"""Bundle source and the public reference used by the desktop app.

The Indic checkpoint is downloaded and hash-verified by prepare_build.py.
Keeping it out of this source archive avoids duplicating a 278 MB model.
"""
from pathlib import Path
import shutil
import zipfile

root = Path(__file__).resolve().parent
app = root / "dist" / "FemaleVocalIndic"
for name in (
    "README.txt", "LICENSE", "MODEL-LICENSE.txt", "SEEDVC-LICENSE.txt",
    "REFERENCE-VOICE-SOURCE.txt", "THIRD-PARTY-NOTICES.txt",
    "PYRNNOISE-LICENSE.txt", "RNNOISE-LICENSE.txt",
):
    shutil.copy2(root / name, app / name)

source = root / "dist" / "FemaleVocalIndic-source.zip"
excluded = {
    "assets", "build", "dist", "release", ".vendor-rvc", ".vendor-seedvc",
    "__pycache__", ".git", ".venv-seedvc", ".venv-build", ".venv", "examples",
}
with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if path.is_file() and not excluded.intersection(relative.parts) and path.suffix != ".pyc":
            archive.write(path, "FemaleVocal-source/" + relative.as_posix())
    for name in ("assets/reference/female-reference.wav",):
        path = root / name
        archive.write(path, "FemaleVocal-source/" + path.relative_to(root).as_posix())
shutil.copy2(source, app / source.name)

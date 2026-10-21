"""Bundle corresponding app and patched inference sources with the desktop app."""
from pathlib import Path
import shutil
import zipfile
root = Path(__file__).resolve().parent
app = root / "dist/FreeVoice"
for name in ("README.txt", "LICENSE", "MODEL-LICENSE.txt", "RVC-LICENSE.txt", "THIRD-PARTY-NOTICES.txt"):
    shutil.copy2(root / name, app / name)
source = root / "dist/FreeVoice-source.zip"
excluded = {"assets", "build", "dist", "release", ".vendor-rvc", "__pycache__", ".git"}
with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if path.is_file() and not excluded.intersection(relative.parts) and path.suffix != ".pyc":
            archive.write(path, "FreeVoice-source/" + relative.as_posix())
shutil.copy2(source, app / source.name)

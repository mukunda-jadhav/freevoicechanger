"""Fetch pinned inference sources and verified public model assets for a clean build."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
REVISION = "81eed5e8f68b6bed1789f682fe78cdd324495afc"
vendor = ROOT / ".vendor-rvc"
if not vendor.exists():
    subprocess.run(["git", "clone", "https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git", str(vendor)], check=True)
subprocess.run(["git", "checkout", REVISION], cwd=vendor, check=True)
for folder in ("infer", "tools", "configs", "i18n"):
    shutil.copytree(vendor / folder, ROOT / folder, dirs_exist_ok=True)
shutil.copyfile(vendor / "LICENSE", ROOT / "RVC-LICENSE.txt")
realtime = ROOT / "infer/rtrvc.py"
realtime.write_text(realtime.read_text(encoding="utf-8").replace("np.square(1 / score)", "np.square(1 / np.maximum(score, 1e-8))"), encoding="utf-8")
for asset in json.loads((ROOT / "model-assets.json").read_text()):
    target = ROOT / asset["destination"]
    target.parent.mkdir(parents=True, exist_ok=True)
    def valid():
        if not target.exists():
            return False
        with target.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest() == asset["sha256"]
    if valid():
        continue
    partial = target.with_name(target.name + ".part")
    subprocess.run(["curl.exe", "-L", "--fail", "--retry", "5", "--retry-all-errors", "-C", "-", "-o", str(partial), asset["url"]], check=True)
    partial.replace(target)
    if not valid():
        raise RuntimeError(f"Hash mismatch for {target.name}")
print("Sources and models ready.")

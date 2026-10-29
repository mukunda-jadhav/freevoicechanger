"""Verify the public model and prepare the Seed-VC realtime sources."""
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

ROOT = Path(__file__).resolve().parent
SEED = ROOT / "seedvc_backend" / "seed-vc-realtime"
if not (SEED / "realtime_vc_engine.py").exists():
    raise FileNotFoundError("Seed-VC runtime source is missing from this source folder.")

engine = SEED / "realtime_vc_engine.py"
text = engine.read_text(encoding="utf-8")
text = text.replace("from funasr import AutoModel\n", "")
text = text.replace(
    '        self.vad_model = AutoModel(model="fsmn-vad", model_revision="v2.0.4", disable_pbar=True, log_level="ERROR", disable_update=True)\n',
    ""
)
text = text.replace(
    '        cuda_target = f"cuda:{gpu_id}" if gpu_id else "cuda"\n        if torch.cuda.is_available():',
    '        if str(gpu_id).lower() == "cpu":\n            return torch.device("cpu")\n        cuda_target = f"cuda:{gpu_id}" if gpu_id else "cuda"\n        if torch.cuda.is_available():',
    1,
)
if "# VAD Processing" in text:
    start = text.index("        # VAD Processing\n", text.index("    def _process_block(self, indata):"))
    end = text.index("        # Preprocessing\n", start)
    text = text[:start] + """        suppressor = getattr(self, "input_suppressor", None)
        if suppressor is not None:
            clean_48k = librosa.resample(indata, orig_sr=self.config.samplerate, target_sr=48000)
            clean_48k = suppressor.process(clean_48k)
            indata = librosa.resample(clean_48k, orig_sr=48000, target_sr=self.config.samplerate).astype(np.float32, copy=False)
        rms = float(np.sqrt(np.mean(np.square(indata, dtype=np.float32))))
        if rms >= 0.003:
            self.last_speech_time = time.monotonic()
        self.vad_speech_detected = time.monotonic() - getattr(self, "last_speech_time", 0.0) < 0.35

""" + text[end:]
if "from funasr import AutoModel" in text or "self.vad_model = AutoModel(" in text:
    raise RuntimeError("Could not remove the heavyweight VAD path.")
engine.write_text(text, encoding="utf-8", newline="")

hf = SEED / "hf_utils.py"
h = hf.read_text(encoding="utf-8")
if "CACHE_DIR = " not in h:
    h = h.replace(
        "import os\nfrom huggingface_hub import hf_hub_download\n",
        "import os\nfrom pathlib import Path\nfrom huggingface_hub import hf_hub_download\n\nCACHE_DIR = Path(os.environ.get('HF_HOME', Path.home() / '.cache' / 'huggingface')) / 'seed-vc-realtime'\nCACHE_DIR.mkdir(parents=True, exist_ok=True)\n",
        1,
    )
h = h.replace('cache_dir="./checkpoints"', "cache_dir=str(CACHE_DIR)")
hf.write_text(h, encoding="utf-8", newline="")

asset = json.loads((ROOT / "model-assets.json").read_text(encoding="utf-8"))[0]
target = ROOT / asset["destination"]
target.parent.mkdir(parents=True, exist_ok=True)
def valid(path):
    if not path.exists():
        return False
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() == asset["sha256"]
if not valid(target):
    partial = target.with_name(target.name + ".part")
    import subprocess
    subprocess.run(["curl.exe", "-L", "--fail", "--retry", "5", "--retry-all-errors", "-C", "-", "-o", str(partial), asset["url"]], check=True)
    if not valid(partial):
        raise RuntimeError(f"Hash mismatch for {target.name}")
    partial.replace(target)

reference = ROOT / "assets" / "reference" / "female-reference.wav"
reference.parent.mkdir(parents=True, exist_ok=True)
if not reference.exists():
    shutil.copy2(SEED / "examples" / "reference" / "s1p1.wav", reference)
config = ROOT / "seedvc_backend" / "config_dit_mel_seed_uvit_xlsr_tiny.yml"
if not config.exists():
    url = "https://raw.githubusercontent.com/Plachtaa/seed-vc/51383ef/config_dit_mel_seed_uvit_xlsr_tiny.yml"
    config.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, config)
shutil.copy2(SEED / "LICENSE", ROOT / "SEEDVC-LICENSE.txt")
print("Indic checkpoint, reference voice, and Seed-VC sources are ready.")

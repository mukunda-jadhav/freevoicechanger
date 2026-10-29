import os
from pathlib import Path
from huggingface_hub import hf_hub_download

CACHE_DIR = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "seed-vc-realtime"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_custom_model_from_hf(repo_id, model_filename="pytorch_model.bin", config_filename=None):
    os.makedirs("./checkpoints", exist_ok=True)
    model_path = hf_hub_download(repo_id=repo_id, filename=model_filename, cache_dir=str(CACHE_DIR))
    if config_filename is None:
        return model_path
    config_path = hf_hub_download(repo_id=repo_id, filename=config_filename, cache_dir=str(CACHE_DIR))

    return model_path, config_path
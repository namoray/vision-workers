import clip
import constants as cst
import os


class ClipEmbeddingsProcessor:
    def __init__(self):
        device = os.getenv("DEVICE", cst.DEFAULT_DEVICE)
        self.clip_device = device if "cuda" in device else f"cuda:{device}"
        self._clip_model, self._clip_preprocess = clip.load(
            "ViT-B/32", device=self.clip_device
        )

    def get_clip_resources(self):
        return self._clip_model, self._clip_preprocess

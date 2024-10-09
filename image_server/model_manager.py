import os
from huggingface_hub import hf_hub_download
import constants as cst
import base_model

class ModelManager:
    def __init__(self):
        self.last_used_model = None

    def set_last_used_model(self, model_name: str):
        self.last_used_model = model_name

    def get_last_used_model(self) -> str:
        return self.last_used_model

    async def download_model(self, request: base_model.LoadModelRequest) -> base_model.LoadModelResponse:
        local_path = os.path.join(cst.COMFY_CHECKPOINTS_PATH, request.safetensors_filename)
        self.set_last_used_model(request.safetensors_filename)
        if os.path.exists(local_path):
            return base_model.LoadModelResponse(status=base_model.ModelStatus.ALREADY_EXISTS)
        model_path = hf_hub_download(repo_id=request.model_repo, filename=request.safetensors_filename, local_dir=os.path.dirname(local_path))
        return base_model.LoadModelResponse(status=base_model.ModelStatus.SUCCESS)

model_manager = ModelManager()
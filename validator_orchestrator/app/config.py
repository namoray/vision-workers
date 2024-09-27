from pydantic import BaseModel
from typing import List, Dict
import os
from app.core.models import ServerType, ProdDockerImages

DEFAULT_NETWORK_NAME = "comm"


class CheckingServerConfig(BaseModel):
    name: str
    docker_image: str
    port: int
    volumes: Dict[str, str]  # volue name, mount path
    network: str

shared_network = os.getenv("SHARED_NETWORK_NAME", DEFAULT_NETWORK_NAME)

checking_server_configs: list[CheckingServerConfig] = [
        CheckingServerConfig(
            name=ServerType.LLM.value,
            docker_image=os.getenv("LLM_SERVER_DOCKER_IMAGE", ProdDockerImages.LLM),
            port=6919,
            volumes={
                "HF": "/app/cache",
            },
            network=shared_network,
        ),
        CheckingServerConfig(
            name=ServerType.IMAGE.value,
            docker_image=os.getenv("IMAGE_SERVER_DOCKER_IMAGE", ProdDockerImages.IMAGE),
            port=6919,
            volumes={"COMFY": "/app/image_server/ComfyUI"},
            network=shared_network,
        ),
    ]

def get_checking_server_config(server_type: ServerType) -> CheckingServerConfig | None:
    for worker_config in checking_server_configs:
        if worker_config.name == server_type.value:
            return worker_config
    return None




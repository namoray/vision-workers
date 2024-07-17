from pydantic import BaseModel
from typing import List, Dict
import os
from app.models import ServerType, ProdDockerImages

DEFAULT_NETWORK_NAME = "comm"
class WorkerConfig(BaseModel):
    name: str
    docker_image: str
    port: int
    volumes: Dict[str, str] # volue name, mount path
    network: str

class Workers(BaseModel):
    workers: List[WorkerConfig]

shared_network = os.getenv("SHARED_NETWORK_NAME", DEFAULT_NETWORK_NAME)

worker_config = Workers(
    workers=[
        WorkerConfig(
            name=ServerType.LLM,
            docker_image=os.getenv("LLM_SERVER_DOCKER_IMAGE", ProdDockerImages.LLM), 
            port=6919, 
            volumes={
                "HF": "/app/cache",
            },
            network=shared_network
        ),
        WorkerConfig(
            name=ServerType.IMAGE,
            docker_image=os.getenv("IMAGE_SERVER_DOCKER_IMAGE", ProdDockerImages.IMAGE), 
            port=6919, 
            volumes={
                "COMFY": "/app/image_server/ComfyUI"
            },
            network=shared_network
        )
    ]
)
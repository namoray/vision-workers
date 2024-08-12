from pydantic_settings import BaseSettings
from app import models
from app.synthetic import synthetic_generation
from app.checking import checking_functions
from app import utility_models
from enum import Enum
from app.constants import BASE_URL


class Settings(BaseSettings):
    version: str = "1.0.0"
    environment: str = "prod"
    debug: bool = False
    cors_origins: list[str] = ["*"]


class Endpoints(Enum):
    text_to_image = "/txt2img"
    image_to_image = "/img2img"
    avatar = "/avatar"
    inpaint = "/inpaint"
    upscale = "/upscale"
    clip_embeddings = "/clip-embeddings"


settings = Settings()


task_configs = models.TaskConfigMapping(
    tasks={
        models.Tasks.chat_mixtral.value: models.TaskConfig(
            server_needed=models.ServerType.LLM,
            load_model_config=models.ModelConfigDetails(
                model="TheBloke/Nous-Hermes-2-Mixtral-8x7B-DPO-GPTQ",
                half_precision=True,
                revision="gptq-8bit-128g-actorder_True",
            ),
            endpoint=BASE_URL + "/generate_text",
            checking_function=checking_functions.check_text_result,
            synthetic_generation_function=synthetic_generation.generate_chat_synthetic,
            synthetic_generation_params={
                "model": utility_models.ChatModels.mixtral.value
            },
            task=models.Tasks.chat_mixtral,
        ),
        models.Tasks.chat_llama_3.value: models.TaskConfig(
            server_needed=models.ServerType.LLM,
            load_model_config=models.ModelConfigDetails(
                model="casperhansen/llama-3-70b-instruct-awq",
                tokenizer="tau-vision/llama-3-tokenizer-fix",
                half_precision=True,
            ),
            endpoint=BASE_URL + "/generate_text",
            checking_function=checking_functions.check_text_result,
            synthetic_generation_function=synthetic_generation.generate_chat_synthetic,
            synthetic_generation_params={
                "model": utility_models.ChatModels.llama_3.value
            },
            task=models.Tasks.chat_llama_3,
        ),
        models.Tasks.chat_llama_31_8b.value: models.TaskConfig(
            server_needed=models.ServerType.LLM,
            load_model_config=models.ModelConfigDetails(
                model="unsloth/Meta-Llama-3.1-8B-Instruct",
                tokenizer="tau-vision/llama-tokenizer-fix",
                half_precision=True,
                max_model_len=16000,
            ),
            endpoint=BASE_URL + "/generate_text",
            checking_function=checking_functions.check_text_result,
            synthetic_generation_function=synthetic_generation.generate_chat_synthetic,
            synthetic_generation_params={
                "model": utility_models.ChatModels.llama_31_8b.value
            },
            task=models.Tasks.chat_llama_31_8b,
        ),
        models.Tasks.chat_llama_31_70b.value: models.TaskConfig(
            server_needed=models.ServerType.LLM,
            load_model_config=models.ModelConfigDetails(
                model="hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4",
                tokenizer="tau-vision/llama-tokenizer-fix",
                half_precision=True,
                gpu_memory_utilization=0.85,
                max_model_len=16000,
            ),
            endpoint=BASE_URL + "/generate_text",
            checking_function=checking_functions.check_text_result,
            synthetic_generation_function=synthetic_generation.generate_chat_synthetic,
            synthetic_generation_params={
                "model": utility_models.ChatModels.llama_31_70b.value
            },
            task=models.Tasks.chat_llama_31_70b,
        ),
        models.Tasks.proteus_text_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.text_to_image.value,
            checking_function=checking_functions.check_image_result,
            synthetic_generation_function=synthetic_generation.generate_text_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.PROTEUS.value
            },
            task=models.Tasks.proteus_text_to_image,
        ),

        models.Tasks.flux_schnell_text_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.text_to_image.value,
            checking_function=checking_functions.check_image_result,
            synthetic_generation_function=synthetic_generation.generate_text_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.FLUX_SCHNELL.value
            },
            task=models.Tasks.flux_schnell_text_to_image,
        ),
        models.Tasks.playground_text_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.text_to_image.value,
            checking_function=checking_functions.check_image_result,
            synthetic_generation_function=synthetic_generation.generate_text_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.PLAYGROUND.value
            },
            task=models.Tasks.playground_text_to_image,
        ),
        models.Tasks.playground_text_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.text_to_image.value,
            checking_function=checking_functions.check_image_result,
            synthetic_generation_function=synthetic_generation.generate_text_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.PLAYGROUND.value
            },
            task=models.Tasks.playground_text_to_image,
        ),
        models.Tasks.dreamshaper_text_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.text_to_image.value,
            checking_function=checking_functions.check_image_result,
            synthetic_generation_function=synthetic_generation.generate_text_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.DREAMSHAPER.value
            },
            task=models.Tasks.dreamshaper_text_to_image,
        ),
        models.Tasks.proteus_image_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.image_to_image.value,
            checking_function=checking_functions.check_image_result,
            synthetic_generation_function=synthetic_generation.generate_image_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.PROTEUS.value
            },
            task=models.Tasks.proteus_image_to_image,
        ),
        models.Tasks.playground_image_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.image_to_image.value,
            checking_function=checking_functions.check_image_result,
            synthetic_generation_function=synthetic_generation.generate_image_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.PLAYGROUND.value
            },
            task=models.Tasks.playground_image_to_image,
        ),
        models.Tasks.flux_schnell_image_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.image_to_image.value,
            checking_function=checking_functions.check_image_result,
            synthetic_generation_function=synthetic_generation.generate_image_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.FLUX_SCHNELL.value
            },
            task=models.Tasks.flux_schnell_image_to_image,
        ),
        models.Tasks.dreamshaper_image_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.image_to_image.value,
            checking_function=checking_functions.check_image_result,
            synthetic_generation_function=synthetic_generation.generate_image_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.DREAMSHAPER.value
            },
            task=models.Tasks.dreamshaper_image_to_image,
        ),
        models.Tasks.avatar.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.avatar.value,
            checking_function=checking_functions.check_image_result,
            synthetic_generation_function=synthetic_generation.generate_avatar_synthetic,
            synthetic_generation_params={},
            task=models.Tasks.avatar,
        ),
        models.Tasks.jugger_inpainting.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.inpaint.value,
            checking_function=checking_functions.check_image_result,
            synthetic_generation_function=synthetic_generation.generate_inpaint_synthetic,
            synthetic_generation_params={},
            task=models.Tasks.jugger_inpainting,
        ),
        # models.Tasks.upscale.value: models.TaskConfig(
        #     server_needed=models.ServerType.IMAGE,
        #     load_model_config=None,
        #     endpoint=BASE_URL + Endpoints.upscale.value,
        #     checking_function=checking_functions.check_image_result,
        #     synthetic_generation_function=synthetic_generation.generate_upscale_synthetic,
        #     synthetic_generation_params={},
        #     task=models.Tasks.upscale,
        # ),
        models.Tasks.clip_image_embeddings.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.clip_embeddings.value,
            checking_function=checking_functions.check_clip_result,
            synthetic_generation_function=synthetic_generation.generate_clip_synthetic,
            synthetic_generation_params={},
            task=models.Tasks.clip_image_embeddings,
        ),
    }
)

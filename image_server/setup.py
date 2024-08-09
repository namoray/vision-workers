import os
import subprocess
from typing import Optional
import asyncio
import huggingface_hub

async def clone_repo(repo_url: str, target_dir: str, commit_hash: Optional[str] = None) -> None:
    if not os.path.exists(target_dir) or not os.listdir(target_dir):
        await asyncio.to_thread(subprocess.run, ['git', 'clone', '--depth', '1', repo_url, target_dir], check=True)
        if commit_hash:
            await asyncio.to_thread(subprocess.run, ['git', 'fetch', '--depth', '1', 'origin', commit_hash], cwd=target_dir, check=True)
            await asyncio.to_thread(subprocess.run, ['git', 'checkout', commit_hash], cwd=target_dir, check=True)

async def download_file(*, repo_id: str, filename: str, local_dir: str, cache_dir: str) -> None:
    os.makedirs(local_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    await asyncio.to_thread(
        huggingface_hub.hf_hub_download,
        repo_id=repo_id,
        filename=filename,
        local_dir=local_dir,
        cache_dir=cache_dir,
    )

async def main():
    await clone_repo(repo_url='https://github.com/comfyanonymous/ComfyUI.git', target_dir='ComfyUI', commit_hash='f7a5107784cded39f92a4bb7553507575e78edbe')

    download_tasks = [
        download_file(repo_id='tau-vision/jugger-inpaint', filename='juggerinpaint.safetensors', local_dir='ComfyUI/models/checkpoints', cache_dir='ComfyUI/models/caches'),
        download_file(repo_id='Lykon/dreamshaper-xl-v2-turbo', filename='DreamShaperXL_Turbo_v2_1.safetensors', local_dir='ComfyUI/models/checkpoints', cache_dir='ComfyUI/models/caches'),
        download_file(repo_id='dataautogpt3/ProteusV0.4-Lightning', filename='ProteusV0.4-Lighting.safetensors', local_dir='ComfyUI/models/checkpoints', cache_dir='ComfyUI/models/caches'),
        download_file(repo_id='playgroundai/playground-v2.5-1024px-aesthetic', filename='playground-v2.5-1024px-aesthetic.fp16.safetensors', local_dir='ComfyUI/models/checkpoints', cache_dir='ComfyUI/models/caches'),
        download_file(repo_id='comfyanonymous/flux_text_encoders', filename='t5xxl_fp8_e4m3fn.safetensors', local_dir='ComfyUI/models/clip', cache_dir='ComfyUI/models/caches'),
        download_file(repo_id='comfyanonymous/flux_text_encoders', filename='clip_l.safetensors', local_dir='ComfyUI/models/clip', cache_dir='ComfyUI/models/caches'),
        download_file(repo_id='black-forest-labs/FLUX.1-schnell', filename='ae.safetensors', local_dir='ComfyUI/models/vae', cache_dir='ComfyUI/models/caches'),
        download_file(repo_id='black-forest-labs/FLUX.1-schnell', filename='flux1-schnell.safetensors', local_dir='ComfyUI/models/unet', cache_dir='ComfyUI/models/caches'),
        download_file(repo_id='Corcelio/flux-dev-unet', filename='flux1-dev.sft', local_dir='ComfyUI/models/unet', cache_dir='ComfyUI/models/caches'),
        download_file(repo_id='gsdf/CounterfeitXL', filename='embeddings/negativeXL_A.safetensors', local_dir='ComfyUI/models/embeddings', cache_dir='ComfyUI/models/caches'),
        download_file(repo_id='madebyollin/sdxl-vae-fp16-fix', filename='sdxl.vae.safetensors', local_dir='ComfyUI/models/vae', cache_dir='ComfyUI/models/caches'),
    ]

    await asyncio.gather(*download_tasks)

    if not os.path.exists('ComfyUI/input/init.png'):
        os.rename('ComfyUI/input/example.png', 'ComfyUI/input/init.png')
    if not os.path.exists('ComfyUI/input/mask.png'):
        await asyncio.to_thread(subprocess.run, ['cp', 'ComfyUI/input/init.png', 'ComfyUI/input/mask.png'], check=True)

    clone_tasks = [
        clone_repo(repo_url='https://github.com/ltdrdata/ComfyUI-Inspire-Pack', target_dir='ComfyUI/custom_nodes/ComfyUI-Inspire-Pack', commit_hash='985f6a239b1aed0c67158f64bf579875ec292cb2'),
        clone_repo(repo_url='https://github.com/cubiq/ComfyUI_IPAdapter_plus', target_dir='ComfyUI/custom_nodes/ComfyUI_IPAdapter_plus', commit_hash='0d0a7b3693baf8903fe2028ff218b557d619a93d'),
        clone_repo(repo_url='https://github.com/cubiq/ComfyUI_InstantID', target_dir='ComfyUI/custom_nodes/ComfyUI_InstantID', commit_hash='50445991e2bd1d5ec73a8633726fe0b33a825b5b'),
    ]

    await asyncio.gather(*clone_tasks)

    await download_file(repo_id='tau-vision/insightface-antelopev2', filename='antelopev2.zip', local_dir='ComfyUI/models/insightface/models', cache_dir='ComfyUI/models/caches')
    if not os.path.exists('ComfyUI/models/insightface/models/antelopev2'):
        await asyncio.to_thread(subprocess.run, ['unzip', 'ComfyUI/models/insightface/models/antelopev2.zip', '-d', 'ComfyUI/models/insightface/models'], check=True)

    final_downloads = [
        download_file(repo_id='InstantX/InstantID', filename='ip-adapter.bin', local_dir='ComfyUI/models/instantid', cache_dir='ComfyUI/models/caches'),
        download_file(repo_id='InstantX/InstantID', filename='ControlNetModel/diffusion_pytorch_model.safetensors', local_dir='ComfyUI/models/controlnet', cache_dir='ComfyUI/models/caches'),
    ]

    await asyncio.gather(*final_downloads)

    print("Setup completed successfully.")

if __name__ == "__main__":
    asyncio.run(main())

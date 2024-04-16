if [ ! -d ComfyUI ]; then 
  git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git
  cd ComfyUI
  git fetch --depth 1 origin 45ec1cbe963055798765645c4f727122a7d3e35e
  git checkout 45ec1cbe963055798765645c4f727122a7d3e35e
  cd ..
fi

[ -f ComfyUI/models/checkpoints/juggerinpaint.safetensors ] || wget -O ComfyUI/models/checkpoints/juggerinpaint.safetensors https://huggingface.co/diagonalge/juggernaut-inpaint/resolve/main/juggerinpaint.safetensors?download=true

[ -f ComfyUI/models/checkpoints/dreamshaperturbo.safetensors ] || wget -O ComfyUI/models/checkpoints/dreamshaperturbo.safetensors https://huggingface.co/Lykon/dreamshaper-xl-v2-turbo/resolve/main/DreamShaperXL_Turbo_v2_1.safetensors?download=true

[ -f ComfyUI/models/checkpoints/proteus.safetensors ] || wget -O ComfyUI/models/checkpoints/proteus.safetensors https://huggingface.co/dataautogpt3/ProteusV0.4-Lightning/resolve/main/ProteusV0.4-Lighting.safetensors?download=true

[ -f ComfyUI/models/checkpoints/playground.safetensors ] || wget -O ComfyUI/models/checkpoints/playground.safetensors https://huggingface.co/playgroundai/playground-v2.5-1024px-aesthetic/resolve/main/playground-v2.5-1024px-aesthetic.fp16.safetensors?download=true

[ -f ComfyUI/models/embeddings/negativeXL_A.safetensors ] || wget -O ComfyUI/models/embeddings/negativeXL_A.safetensors https://huggingface.co/gsdf/CounterfeitXL/resolve/main/embeddings/negativeXL_A.safetensors?download=true

[ -f ComfyUI/models/vae/sdxl_vae.safetensors ] || wget -O ComfyUI/models/vae/sdxl_vae.safetensors https://huggingface.co/madebyollin/sdxl-vae-fp16-fix/resolve/main/sdxl.vae.safetensors?download=true

[ -f ComfyUI/models/upscale_models/ultrasharp.pt ] || wget -O ComfyUI/models/upscale_models/ultrasharp.pt https://civitai.com/api/download/models/125843

[ -f ComfyUI/input/init.png ] || cp assets/face_image.png ComfyUI/input/init.png

cd ComfyUI/custom_nodes

[ -d ComfyUI-Inspire-Pack ] || git clone https://github.com/ltdrdata/ComfyUI-Inspire-Pack

[ -d ComfyUI_IPAdapter_plus ] || git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus

if [ ! -d ComfyUI_InstantID ]; then 
  git clone https://github.com/cubiq/ComfyUI_InstantID
  cd ComfyUI_InstantID
  git checkout 8b7932a66bf43b5e2499e2ba77df5c373af006da
  cd ..
fi

cd ../..

mkdir -p ComfyUI/models/insightface/models

cd ComfyUI/models/insightface/models

[ -f antelopev2.zip ] || gdown 18wEUfMNohBJ4K3Ly5wpTejPfDzp-8fI8

[ -d antelopev2 ] || unzip antelopev2.zip

cd ../../../..

mkdir -p ComfyUI/models/instantid

cd ComfyUI/models/instantid

[ -f ip-adapter.bin ] || wget -O ip-adapter.bin https://huggingface.co/InstantX/InstantID/resolve/main/ip-adapter.bin?download=true

cd ../../..

[ ! -d "ComfyUI/models/controlnet" ] && mkdir ComfyUI/models/controlnet
cd ComfyUI/models/controlnet

[ -f diffusion_pytorch_model.safetensors ] || wget -O diffusion_pytorch_model.safetensors https://huggingface.co/InstantX/InstantID/resolve/main/ControlNetModel/diffusion_pytorch_model.safetensors?download=true

cd ../../..

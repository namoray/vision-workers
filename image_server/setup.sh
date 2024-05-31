if [ ! -d ComfyUI ]; then 
  git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git
  cd ComfyUI
  git fetch --depth 1 origin 57753c964affd18d2b87d2a47fe6b375bca39004
  git checkout 57753c964affd18d2b87d2a47fe6b375bca39004
  cd ..
fi

[ -f ComfyUI/models/checkpoints/juggerinpaint.safetensors ] || wget -O ComfyUI/models/checkpoints/juggerinpaint.safetensors https://huggingface.co/tau-vision/jugger-inpaint/resolve/main/juggerinpaint.safetensors?download=true

[ -f ComfyUI/models/checkpoints/dreamshaperturbo.safetensors ] || wget -O ComfyUI/models/checkpoints/dreamshaperturbo.safetensors https://huggingface.co/Lykon/dreamshaper-xl-v2-turbo/resolve/main/DreamShaperXL_Turbo_v2_1.safetensors?download=true

[ -f ComfyUI/models/checkpoints/proteus.safetensors ] || wget -O ComfyUI/models/checkpoints/proteus.safetensors https://huggingface.co/dataautogpt3/ProteusV0.4-Lightning/resolve/main/ProteusV0.4-Lighting.safetensors?download=true

[ -f ComfyUI/models/checkpoints/playground.safetensors ] || wget -O ComfyUI/models/checkpoints/playground.safetensors https://huggingface.co/playgroundai/playground-v2.5-1024px-aesthetic/resolve/main/playground-v2.5-1024px-aesthetic.fp16.safetensors?download=true

[ -f ComfyUI/models/embeddings/negativeXL_A.safetensors ] || wget -O ComfyUI/models/embeddings/negativeXL_A.safetensors https://huggingface.co/gsdf/CounterfeitXL/resolve/main/embeddings/negativeXL_A.safetensors?download=true

[ -f ComfyUI/models/vae/sdxl_vae.safetensors ] || wget -O ComfyUI/models/vae/sdxl_vae.safetensors https://huggingface.co/madebyollin/sdxl-vae-fp16-fix/resolve/main/sdxl.vae.safetensors?download=true

[ -f ComfyUI/models/upscale_models/ultrasharp.pt ] || wget -O ComfyUI/models/upscale_models/ultrasharp.pt https://civitai.com/api/download/models/125843

[ -f ComfyUI/input/init.png ] || mv ComfyUI/input/example.png ComfyUI/input/init.png

[ -f ComfyUI/input/mask.png ] || cp ComfyUI/input/init.png ComfyUI/input/mask.png

cd ComfyUI/custom_nodes

if [ ! -d ComfyUI-Inspire-Pack ]; then 
  git clone https://github.com/ltdrdata/ComfyUI-Inspire-Pack
  cd ComfyUI-Inspire-Pack
  git checkout 985f6a239b1aed0c67158f64bf579875ec292cb2
  cd ..
fi

if [ ! -d ComfyUI_IPAdapter_plus ]; then 
  git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus
  cd ComfyUI_IPAdapter_plus
  git checkout 0d0a7b3693baf8903fe2028ff218b557d619a93d
  cd ..
fi

if [ ! -d ComfyUI_InstantID ]; then 
  git clone https://github.com/cubiq/ComfyUI_InstantID
  cd ComfyUI_InstantID
  git checkout 50445991e2bd1d5ec73a8633726fe0b33a825b5b
  cd ..
fi

if [ ! -d comfyui-tooling-nodes ]; then 
  git clone https://github.com/Acly/comfyui-tooling-nodes
  cd comfyui-tooling-nodes
  git checkout 96dd277b533d71cdfdc5f01b98899045315b56e7
  cd ..
fi

cd ../..

mkdir -p ComfyUI/models/insightface/models

cd ComfyUI/models/insightface/models

[ -f antelopev2.zip ] || wget -O antelopev2.zip https://huggingface.co/tau-vision/insightface-antelopev2/resolve/main/antelopev2.zip

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

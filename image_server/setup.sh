#!/bin/bash

# Function to get LFS sha256 hash
get_lfs_sha256() {
    local repo_url=$1
    local file_path=$2
    
    # Clone only the LFS pointers without downloading the actual files
    tmp_dir=$(mktemp -d)
    git clone --no-checkout --filter=blob:none $repo_url $tmp_dir
    
    cd $tmp_dir
    git checkout HEAD -- $file_path
    
    # Extract the SHA256 from the LFS pointer file
    sha256=$(cat $file_path | grep -oP '(?<=sha256:)[a-f0-9]{64}')
    
    cd - > /dev/null
    rm -rf $tmp_dir
    
    echo $sha256
}

# Function to download file if it doesn't exist or has wrong hash
download_file() {
    local file=$1
    local url=$2
    local repo_url=$3
    local file_path=$4
    local temp_file="${file}.tmp"

    expected_hash=$(get_lfs_sha256 $repo_url $file_path)

    if [ -f "$file" ]; then
        local_hash=$(sha256sum "$file" | awk '{print $1}')
        if [ "$local_hash" = "$expected_hash" ]; then
            echo "File $file exists and has correct hash. Skipping download."
            return
        else
            echo "File $file exists but has incorrect hash. Re-downloading."
        fi
    else
        echo "File $file does not exist. Downloading."
    fi

    wget -O "$temp_file" "$url"
    downloaded_hash=$(sha256sum "$temp_file" | awk '{print $1}')

    if [ "$downloaded_hash" = "$expected_hash" ]; then
        mv "$temp_file" "$file"
        echo "File $file downloaded successfully and verified."
    else
        echo "Downloaded file $file has incorrect hash. Please check the source and try again."
        rm "$temp_file"
        exit 1
    fi
}

# ComfyUI setup
if [ ! -d ComfyUI ] || [ -z "$(ls -A ComfyUI)" ]; then 
  git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git ComfyUI
  cd ComfyUI
  git fetch --depth 1 origin 57753c964affd18d2b87d2a47fe6b375bca39004
  git checkout 57753c964affd18d2b87d2a47fe6b375bca39004
  cd ..
fi

# Download checkpoints
download_file "ComfyUI/models/checkpoints/juggerinpaint.safetensors" \
              "https://huggingface.co/tau-vision/jugger-inpaint/resolve/main/juggerinpaint.safetensors?download=true" \
              "https://huggingface.co/tau-vision/jugger-inpaint" \
              "juggerinpaint.safetensors"

download_file "ComfyUI/models/checkpoints/dreamshaperturbo.safetensors" \
              "https://huggingface.co/Lykon/dreamshaper-xl-v2-turbo/resolve/main/DreamShaperXL_Turbo_v2_1.safetensors?download=true" \
              "https://huggingface.co/Lykon/dreamshaper-xl-v2-turbo" \
              "DreamShaperXL_Turbo_v2_1.safetensors"

download_file "ComfyUI/models/checkpoints/proteus.safetensors" \
              "https://huggingface.co/dataautogpt3/ProteusV0.4-Lightning/resolve/main/ProteusV0.4-Lighting.safetensors?download=true" \
              "https://huggingface.co/dataautogpt3/ProteusV0.4-Lightning" \
              "ProteusV0.4-Lighting.safetensors"

download_file "ComfyUI/models/checkpoints/playground.safetensors" \
              "https://huggingface.co/playgroundai/playground-v2.5-1024px-aesthetic/resolve/main/playground-v2.5-1024px-aesthetic.fp16.safetensors?download=true" \
              "https://huggingface.co/playgroundai/playground-v2.5-1024px-aesthetic" \
              "playground-v2.5-1024px-aesthetic.fp16.safetensors"

# Download embeddings
download_file "ComfyUI/models/embeddings/negativeXL_A.safetensors" \
              "https://huggingface.co/gsdf/CounterfeitXL/resolve/main/embeddings/negativeXL_A.safetensors?download=true" \
              "https://huggingface.co/gsdf/CounterfeitXL" \
              "embeddings/negativeXL_A.safetensors"

# Download VAE
download_file "ComfyUI/models/vae/sdxl_vae.safetensors" \
              "https://huggingface.co/madebyollin/sdxl-vae-fp16-fix/resolve/main/sdxl.vae.safetensors?download=true" \
              "https://huggingface.co/madebyollin/sdxl-vae-fp16-fix" \
              "sdxl.vae.safetensors"

download_file "ComfyUI/models/upscale_models/ultrasharp.pt" \
              "https://huggingface.co/Corcelio/upscale/resolve/main/ultrasharp.pt?download=true" \
              "https://huggingface.co/Corcelio/upscale" \
              "ultrasharp.pt"

# Set up input images
[ -f ComfyUI/input/init.png ] || mv ComfyUI/input/example.png ComfyUI/input/init.png
[ -f ComfyUI/input/mask.png ] || cp ComfyUI/input/init.png ComfyUI/input/mask.png

# Custom nodes setup
cd ComfyUI/custom_nodes

if [ ! -d ComfyUI-Inspire-Pack ] || [ -z "$(ls -A ComfyUI-Inspire-Pack)" ]; then 
  git clone https://github.com/ltdrdata/ComfyUI-Inspire-Pack
  cd ComfyUI-Inspire-Pack
  git checkout 985f6a239b1aed0c67158f64bf579875ec292cb2
  cd ..
fi

if [ ! -d ComfyUI_IPAdapter_plus ] || [ -z "$(ls -A ComfyUI_IPAdapter_plus)" ]; then 
  git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus
  cd ComfyUI_IPAdapter_plus
  git checkout 0d0a7b3693baf8903fe2028ff218b557d619a93d
  cd ..
fi

if [ ! -d ComfyUI_InstantID ] || [ -z "$(ls -A ComfyUI_InstantID)" ]; then 
  git clone https://github.com/cubiq/ComfyUI_InstantID
  cd ComfyUI_InstantID
  git checkout 50445991e2bd1d5ec73a8633726fe0b33a825b5b
  cd ..
fi

cd ../..

# InsightFace models setup
mkdir -p ComfyUI/models/insightface/models
cd ComfyUI/models/insightface/models

download_file "antelopev2.zip" \
              "https://huggingface.co/tau-vision/insightface-antelopev2/resolve/main/antelopev2.zip" \
              "https://github.com/tau-vision/insightface-antelopev2" \
              "antelopev2.zip"

[ -d antelopev2 ] || unzip antelopev2.zip

cd ../../../..

# InstantID models setup
mkdir -p ComfyUI/models/instantid
cd ComfyUI/models/instantid

download_file "ip-adapter.bin" \
              "https://huggingface.co/InstantX/InstantID/resolve/main/ip-adapter.bin?download=true" \
              "https://github.com/InstantX/InstantID" \
              "ip-adapter.bin"

cd ../../..

# ControlNet setup
mkdir -p ComfyUI/models/controlnet
cd ComfyUI/models/controlnet

download_file "diffusion_pytorch_model.safetensors" \
              "https://huggingface.co/InstantX/InstantID/resolve/main/ControlNetModel/diffusion_pytorch_model.safetensors?download=true" \
              "https://github.com/InstantX/InstantID" \
              "ControlNetModel/diffusion_pytorch_model.safetensors"

cd ../../..

echo "Setup completed successfully."
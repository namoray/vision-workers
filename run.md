```bash
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 6919:6919 \
    --ipc=host \
    vllm/vllm-openai:v0.6.3 \
    --model sophosympatheia/Rogue-Rose-103b-v0.2 \
    --revision exl2-3.2bpw \
    --max_model_len 4096 \
    --gpu_memory_utilization 0.7
```


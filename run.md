```bash
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:v0.6.3 \
    --model unsloth/Meta-Llama-3.1-8B-Instruct \
    --tokenizer tau-vision/llama-tokenizer-fix \
    --max_model_len 20000 \
    --gpu_memory_utilization 0.5 \
    --dtype half
```


**Vision LLM inference server**

**WARNING: The LLM server is now only for the validator to use. Please use the same schema as base VLLM
in order to run your miners :)***


Example command to start a base vllm server:
```bash
docker kill vllm_8b || true; docker rm vllm_8b || true; docker run -d --name vllm_8b --runtime nvidia --gpus '"device=0"' \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model unsloth/Meta-Llama-3.1-8B-Instruct \
    --tokenizer tau-vision/llama-tokenizer-fix \
    --gpu-memory-utilization 0.7\
    --max-model-len 20000; docker logs -f --tail 50 vllm_8b
```
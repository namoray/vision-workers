# %%
%load_ext autoreload
%autoreload 2


# %%
import requests
import json
from loguru import logger

def tokenize_message(url, payload):
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
        return None

def generate_completions(url, payload):
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Error: {response.status_code} - {response.text}")
        return None

def main():
    tokenize_url = "http://83.143.115.20:8000/tokenize"
    completions_url = "http://83.143.115.20:8000/v1/completions"

    tokenize_payload = {
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "model": "unsloth/Meta-Llama-3.1-8B-Instruct"
    }

    tokenize_response = tokenize_message(tokenize_url, tokenize_payload)
    if tokenize_response is not None:
        logger.info(tokenize_response)
        completions_payload = {
            "prompt": tokenize_response["tokens"],
            "max_tokens": 10,
            "model": "unsloth/Meta-Llama-3.1-8B-Instruct",
        }
        completions_response = generate_completions(completions_url, completions_payload)
        if completions_response is not None:
            logger.info(completions_response)

main()

# %%
BASE_URL = "http://83.143.115.20:8000"

# %%
import httpx

async def apply_chat_template(messages: list[dict], model: str = "unsloth/Meta-Llama-3.1-8B-Instruct", eot_id: int = 128009, add_generation_prompt: bool = True):
    async with httpx.AsyncClient() as client:
        r = await client.post(url=f"{BASE_URL}/tokenize", json={"model": model, "messages": messages})
        r.raise_for_status()  # raise an exception for 4xx or 5xx status codes
        tokens: list[int] = r.json()["tokens"]
        if "llama-3" in model.lower() and not add_generation_prompt:
            index_of_last_eot_id = max((loc for loc, val in enumerate(tokens) if val == eot_id), default=None)
            if index_of_last_eot_id is not None:
                tokens = tokens[:index_of_last_eot_id]
        
        r2 = await client.post(url=f"{BASE_URL}/detokenize", json={"tokens": tokens, "model": model})
        r2.raise_for_status()  # raise an exception for 4xx or 5xx status codes
        
        prompt = r2.json()["prompt"]
        return prompt, len(tokens)

# %%
async def tokenize(prompt: str, model: str = "unsloth/Meta-Llama-3.1-8B-Instruct"):
    async with httpx.AsyncClient() as client:
        r = await client.post(url=f"{BASE_URL}/tokenize", json={"model": model, "prompt": prompt})
        r.raise_for_status()  # raise an exception for 4xx or 5xx status codes
        return r.json()["tokens"]

# %%
async def detokenize(tokens: list[int], model: str = "unsloth/Meta-Llama-3.1-8B-Instruct"):
    async with httpx.AsyncClient() as client:
        r = await client.post(url=f"{BASE_URL}/detokenize", json={"tokens": tokens, "model": model})
        r.raise_for_status()  # raise an exception for 4xx or 5xx status codes
        return r.json()["prompt"]


# %%
async with httpx.AsyncClient() as client:
    r = await client.post(url=f"{BASE_URL}/detokenize", json={"tokens": [0, 45, 128009, 12, 12, 24], "model": "unsloth/Meta-Llama-3.1-8B-Instruct"})
    r.raise_for_status()  # raise an exception for 4xx or 5xx status codes
    r.json()
r.json()

# %%
def _fjson(r: list[dict]):
    for d in r:
        for p in d.values():
            p["logprob"] = round(float(p["logprob"]), 2)
    return r


# %%
# Get the input prompt & chat messages
input_messages = [    
    {"role": "user", "content": "Hello, how are you? respond in 3 words"},
]
prompt, num_input_tokens = await apply_chat_template(
    messages=input_messages,
    model="unsloth/Meta-Llama-3.1-8B-Instruct",
    eot_id=128009,
    add_generation_prompt=True,
)
prompt, num_input_tokens

# %%
# Get the response from completions
r = requests.post(f"{BASE_URL}/v1/completions", json={
    "prompt": prompt,
    "max_tokens": 30,
    "model": "unsloth/Meta-Llama-3.1-8B-Instruct",
    "temperature": 1.0,
    "include_stop_str_in_output": True,
})

print(r.status_code)
content = json.loads(r.text)["choices"][0]["text"]
content




# %%
# Get the full response
response = prompt + content
response_tokens = await tokenize(response, "unsloth/Meta-Llama-3.1-8B-Instruct")
if response_tokens[-1] != 128009:
    response_tokens.append(128009)
response = await detokenize(response_tokens, "unsloth/Meta-Llama-3.1-8B-Instruct")
chat_response = input_messages + [{"role": "assistant", "content": content}]

# %%
await tokenize(content, "unsloth/Meta-Llama-3.1-8B-Instruct")

# %%
response_tokens

# %%
# Get the prompt logprobs from completions
r = requests.post(f"{BASE_URL}/v1/completions", json={
    "prompt": response,
    "model": "unsloth/Meta-Llama-3.1-8B-Instruct",
    "temperature": 1.0,
    "max_tokens": 1,
    "prompt_logprobs": 2
})

print(r.status_code)
result = json.loads(r.text)
# result["prompt_logprobs"]
result["choices"][0]["prompt_logprobs"][num_input_tokens:]

# %%
prompt_logprobs_to_check = _fjson(result["choices"][0]["prompt_logprobs"][num_input_tokens:])
prompt_logprobs_to_check


# %%
# Check random token

r = requests.post(f"{BASE_URL}/v1/completions", json={
    "prompt": await detokenize(response_tokens[:-2], "unsloth/Meta-Llama-3.1-8B-Instruct"),
    "model": "unsloth/Meta-Llama-3.1-8B-Instruct",
    "temperature": 0.0,
    "max_tokens": 1,
    # "prompt_logprobs": 1,
    "logprobs": 5,
})

print(r.status_code)
result = json.loads(r.text)
result
# result["choices"][0]["prompt_logprobs"][num_input_tokens:]
# result["logprobs"][-1]

# %%
chat_response
fake_chat_response = [{"role": "user", "content": "Hello, how are you? respond in 3 words"}, {"role": "assistant", "content": "I'm doing"}]

# %%
# Check end of token
r = requests.post(f"{BASE_URL}/v1/chat/completions", json={
    "messages": fake_chat_response,
    "model": "unsloth/Meta-Llama-3.1-8B-Instruct",
    "temperature": 0.0,
    "max_tokens": 2,
    "logprobs": True,
    "top_logprobs": 5,
    "add_generation_prompt": True,
    "add_special_tokens": False,
    "include_stop_str_in_output": True,
    "top_k": 5,
})

print(r.status_code)
result = json.loads(r.text)
# result["logprobs"][-1]
result

# %%
r = requests.post(url=f"{BASE_URL}/tokenize", json={
    "model": "unsloth/Meta-Llama-3.1-8B-Instruct",
    "messages": [
        {"role": "user", "content": "Hello, how are you?"},
        # {"role": "assistant", "content": "I am good"},
    ]
})

print(r.status_code, r.text)
print(r.json())

tokens = r.json()["tokens"]

# %%
r = requests.post(url=f"{BASE_URL}/detokenize", json={
    "tokens": tokens,
    "model": "unsloth/Meta-Llama-3.1-8B-Instruct"
})
print(r.status_code, r.text)
print(r.json())

# %%
from sdk import sdk

# %%
await sdk.check_result(task="chat-llama-3-2-3b", orchestrator_url="http://94.156.8.113:6921")



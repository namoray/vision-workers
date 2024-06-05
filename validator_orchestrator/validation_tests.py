import json
import pandas as pd
import asyncio
import numpy as np
import random
import time
import os
import httpx
import re
from app.models import ServerDetails, ServerInstance, ValidationTest, \
    ChatRequestModel, Tasks, CheckResultsRequest, \
    Message, TestInstanceResults, ModelConfigDetails, QueryResult
import requests
from typing import List, Dict, Any, AsyncGenerator, Union

from app.checking.checking_functions import check_text_result

from tenacity import retry, stop_after_attempt, wait_fixed


POST_ENDPOINT = "/generate_text"
SERVERS_JSON_LOC = "tests/servers.json"
PROMPTS_LOC = "tests/test_prompts.txt"
MODELS_TO_TEST_LOC = "tests/models_to_test.json"
TEST_SAVE_LOC = "tests/test_results.csv"
NUMBER_OF_TESTS = 3
VALIDATOR_TASKS = [Tasks.chat_llama_3]

print("Starting script...")

def load_json(file_path: str) -> Dict[str, Any]:
    print(f"Loading JSON from {file_path}")
    with open(file_path) as f:
        return json.load(f)

def load_txt_lines(file_path: str) -> List[str]:
    print(f"Loading text lines from {file_path}")
    with open(file_path, "r") as f:
        return f.readlines()

def get_server_details(servers: Dict[str, Any], server_type: str) -> List[ServerDetails]:
    print(f"Getting server details for {server_type}")
    return [ServerDetails(**server) for server in servers.get(server_type, [])]

def sample_items(items: List[Any], num_needed: int = 1) -> List[Any]:
    print(f"Sampling {num_needed} items from list")
    return random.sample(items, num_needed)

def create_chat_request_samples(prompts: List[str], num_needed: int = 1) -> List[ChatRequestModel]:
    print(f"Creating chat request samples: {num_needed} needed")
    seeds = np.random.randint(0, 50000, num_needed)
    temperatures = [round(temp, 2) for temp in np.random.uniform(0.0, 1.0, num_needed)]
    samples = [ChatRequestModel(messages=[Message(role="user", content=prompt)], seed=seed, top_k=5, temperature=temperature,
                             max_tokens=100, number_of_logprobs=1, starting_assistant_message=True)
            for seed, temperature, prompt in zip(seeds, temperatures, sample_items(prompts, num_needed))]
    print(f"Created samples: {samples}")
    return samples

def create_server_instances(servers: List[ServerDetails], models: List[ModelConfigDetails]) -> List[ServerInstance]:
    print("Creating server instances")
    instances = [ServerInstance(server_details=server, model=model) for server in servers for model in models]
    return instances

def create_validation_tests(validator_server: ServerInstance ,validator_tasks: List[Tasks], miners: List[ServerInstance], prompts: List[str],
                            num_tests: int) -> List[ValidationTest]:
    print(f"Creating validation tests with {num_tests} tests")
    tests = [ValidationTest(validator_server=validator_server, validator_task=validator_task, miners_to_test=miners,
                           prompts_to_check=create_chat_request_samples(prompts, num_tests),
                           checking_function=check_text_result)
            for validator_task in validator_tasks]
    return tests

@retry(stop=stop_after_attempt(3), wait=wait_fixed(300))
async def make_request(server: ServerInstance, payload: Union[ChatRequestModel, CheckResultsRequest], endpoint: str) -> httpx.Response:
    print(f"Making request to {server.server_details.endpoint + endpoint}")
    async with httpx.AsyncClient(timeout=(10, 300)) as client:
        response = await client.post(server.server_details.endpoint + endpoint, json=payload.dict())
        print(f"Response: {response.status_code}, {response.json()}")
        response.raise_for_status()
        return response

@retry(stop=stop_after_attempt(3), wait=wait_fixed(300))
async def make_load_model_request(server: ServerInstance) -> httpx.Response:
    print(f"Making load model request to {server.server_details.endpoint}")
    model_config = server.model
    payload = {
        "model": model_config.model,
        "tokenizer": model_config.tokenizer,
        "revision": model_config.revision
    }
    async with httpx.AsyncClient(timeout=(10, 300)) as client:
        response = await client.post(server.server_details.endpoint + "/load_model", json=payload)
        print('Load model response', response, 'when loading with', payload)
        response.raise_for_status()  
        return response

@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
async def stream_text_from_server(body: dict, url: str) -> AsyncGenerator[str, None]:
    print(f"Streaming text from server: {url + POST_ENDPOINT} with body: {body}")
    async with httpx.AsyncClient(timeout=(10, 300)) as client:
        try:
            async with client.stream("POST", url + POST_ENDPOINT, json=body) as resp:
                print(f"Received response: {resp.status_code}")
                if resp.status_code != 200:
                    raise ValueError(f"Unexpected response status: {resp.status_code}")
                async for chunk in resp.aiter_bytes():
                    try:
                        chunk = chunk.decode()
                        for event in chunk.split("\n\n"):
                            if event == "":
                                continue
                            _, _, data = event.partition(":")
                            if data.strip() == "[DONE]":
                                break
                            loaded_chunk = json.loads(data)
                            text = loaded_chunk["text"]
                            logprob = loaded_chunk["logprobs"][0]["logprob"]
                            yield json.dumps({"text": text, "logprob": logprob})
                    except Exception as e:
                        print(f"Error processing chunk: {e}")
                        continue
        except Exception as e:
            print(f"Error during stream: {e}")

async def process_validation_test(test: ValidationTest) -> None:
    print(f"Processing validation test: {test}")
    test_results = []
    payload_results = {}
    for miner in test.miners_to_test:
        print(f"Loading model for miner: {miner}")
        await make_load_model_request(miner)
        payload_results[miner.model.model] = []
        for prompt in test.prompts_to_check:
            print(f"Streaming text for prompt: {prompt}")
            miner_stream = stream_text_from_server(prompt.dict(), miner.server_details.endpoint)
            response = await _stream_response_from_stream_miners_until_result(miner_stream, miner)
            payload = CheckResultsRequest(task=test.validator_task,
                                          synthetic_query=False,
                                          result=response,
                                          synapse=prompt.dict())
            payload_results[miner.model.model].append(payload.dict())
            print(f"Making check request with payload: {payload}")
            check = await make_request(test.validator_server, payload, "/check-result")
            try:
                score = check.json()["axon_scores"][miner.server_details.id]
                test_res = TestInstanceResults(score=score, miner_server=miner, validator_server=test.validator_server,
                                               messages=prompt.messages, seed=prompt.seed, temperature=prompt.temperature, task=test.validator_task)
                print(test_res.dict())
                test_results.append(test_res)
            except Exception as e:
                print(e)
    save_test_results_to_csv(test_results)
    save_test_results_to_json(payload_results)

def save_test_results_to_json(payload_results: Dict[str, List[Any]]) -> None:
    print("Saving test results to JSON")
    results_to_save = [{"miner_model": model, "payloads": payloads} for model, payloads in payload_results.items()]
    with open(TEST_SAVE_LOC.replace('.csv', '.json'), 'w') as f:
        json.dump(results_to_save, f, indent=4)
    print("Test results saved to JSON")

def save_test_results_to_csv(test_results: List[TestInstanceResults]) -> None:
    print("Saving test results to CSV")
    flattened_results = []
    for result in test_results:
        miner_details = flatten_server_instance_details(result.miner_server)
        res = {'validator': result.validator_server.server_details.endpoint, 'task': result.task, 'score': result.score, 'prompt': result.messages[0].content, 'temp': result.temperature, 'seed': result.seed}
        res.update({f"miner_{k}": v for k, v in miner_details.items()})
        flattened_results.append(res)
    df = pd.DataFrame(flattened_results)
    df.to_csv(TEST_SAVE_LOC, mode='a' if os.path.exists(TEST_SAVE_LOC) else 'w', header=not os.path.exists(TEST_SAVE_LOC), index=False)
    print("Test results saved to CSV")

def flatten_server_instance_details(server_instance: ServerInstance) -> Dict[str, Any]:
    print(f"Flattening server instance details for {server_instance}")
    return {"id": server_instance.server_details.id, "gpu": server_instance.server_details.gpu,
            "endpoint": server_instance.server_details.endpoint, "model_name": server_instance.model.model,
            "model_revision": server_instance.model.revision}

def _load_sse_jsons(chunk: str) -> List[Dict[str, Any]]:
    print(f"Loading SSE JSONs from chunk: {chunk}")
    jsons = []
    received_event_chunks = chunk.split("\n\n")
    for event in received_event_chunks:
        if event == "":
            continue
        prefix, _, data = event.partition(":")
        if data.strip() == "[DONE]":
            break
        loaded_chunk = json.loads(data)
        jsons.append(loaded_chunk)
    return jsons

async def _stream_response_from_stream_miners_until_result(miner_stream: AsyncGenerator[str, None], miner_details: ServerInstance) -> QueryResult:
    print(f"Streaming response from miners until result for {miner_details}")
    time1 = time.time()
    if miner_stream is not None:
        text_data = ""
        async for text in miner_stream:
            if isinstance(text, str):
                text_data += text
        text_jsons = []
        json_objects = re.findall(r'\{.*?\}', text_data)
        for json_obj in json_objects:
            try:
                loaded_data = json.loads(json_obj)
                text_jsons.append(loaded_data)
            except json.JSONDecodeError as e:
                print(f"Skipping invalid JSON data: {json_obj}")
                print(f"Error: {e}")
        if len(text_jsons) > 0:
            return QueryResult(formatted_response=text_jsons, axon_uid=miner_details.server_details.id,
                               failed_axon_uids=[], response_time=time.time() - time1, error_message=None)

async def main():
    print("Running main function")
    servers = load_json(SERVERS_JSON_LOC)
    miners = get_server_details(servers, "miners")
    validators = get_server_details(servers, "validators")
    models = [ModelConfigDetails(**model) for model in load_json(MODELS_TO_TEST_LOC)]
    prompts = load_txt_lines(PROMPTS_LOC)
    miner_servers = create_server_instances(miners, models)
    for validator in validators:
        validation_server = ServerInstance(server_details=validator, model=None)
        test_suite = create_validation_tests(validation_server, VALIDATOR_TASKS, miner_servers, prompts, NUMBER_OF_TESTS)
        for test in test_suite:
            await process_validation_test(test)

if __name__ == "__main__":
    print("Starting asyncio event loop")
    asyncio.run(main())
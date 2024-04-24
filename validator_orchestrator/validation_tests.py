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

POST_ENDPOINT = "/generate_text"
SERVERS_JSON_LOC = "tests/servers.json"
PROMPTS_LOC = "tests/test_prompts.txt"
MODELS_TO_TEST_LOC = "tests/models_to_test.json"
TEST_SAVE_LOC = "tests/test_results.csv"
NUMBER_OF_TESTS = 1

def load_json(file_path: str) -> Dict[str, Any]:
    with open(file_path) as f:
        return json.load(f)

def load_txt_lines(file_path: str) -> List[str]:
    with open(file_path, "r") as f:
        return f.readlines()

def get_server_details(servers: Dict[str, Any], server_type: str) -> List[ServerDetails]:
    return [ServerDetails(**server) for server in servers.get(server_type, [])]

def sample_items(items: List[Any], num_needed: int = 1) -> List[Any]:
    return random.sample(items, num_needed)

def create_chat_request_samples(prompts: List[str], num_needed: int = 1) -> List[ChatRequestModel]:
    seeds = np.random.randint(0, 50000, num_needed)
    temperatures = [round(temp, 2) for temp in np.random.uniform(0.0, 1.0, num_needed)]
    return [ChatRequestModel(messages=[Message(role="user", content=prompt)], seed=seed, top_k=5, temperature=temperature,
                             max_tokens=100, number_of_logprobs=1, starting_assistant_message=True)
            for seed, temperature, prompt in zip(seeds, temperatures, sample_items(prompts, num_needed))]

def create_server_instances(servers: List[ServerDetails], models: List[ModelConfigDetails]) -> List[ServerInstance]:
    return [ServerInstance(server_details=server, model=model) for server in servers for model in models]

def create_validation_tests(validators: List[ServerInstance], miners: List[ServerInstance], prompts: List[str],
                            models: List[ModelConfigDetails], num_tests: int) -> List[ValidationTest]:
    return [ValidationTest(validator_server=validator, miners_to_test=miners,
                           prompts_to_check=create_chat_request_samples(prompts, num_tests),
                           checking_function=check_text_result)
            for validator in validators]

async def make_request(server: ServerInstance, payload: Union[ChatRequestModel, CheckResultsRequest], endpoint: str) -> requests.Response:
    return requests.post(server.server_details.endpoint + endpoint, json=payload.dict())

async def make_load_model_request(server: ServerInstance) -> httpx.Response:
    model_config = server.model
    payload = {
        "model": model_config.model,
        "tokenizer": model_config.tokenizer,
        "revision": model_config.revision
    }
    async with httpx.AsyncClient(timeout=(100000000, 100000000)) as client:
        response = await client.post(server.server_details.endpoint + "/load_model", json=payload)
        if response.status_code == 524:
            time.sleep(600)
        print('Load model response', response, 'when loading with', payload)
    return response

async def stream_text_from_server(body: dict, url: str) -> AsyncGenerator[str, None]:
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url + POST_ENDPOINT, json=body) as resp:
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
                    print(e)

async def process_validation_test(test: ValidationTest) -> None:
    test_results = []
    for miner in test.miners_to_test:
        await make_load_model_request(miner)
        for prompt in test.prompts_to_check:
            miner_stream = stream_text_from_server(prompt.dict(), miner.server_details.endpoint)
            response = await _stream_response_from_stream_miners_until_result(miner_stream, miner)
            check = await make_request(test.validator_server, CheckResultsRequest(task=Tasks.chat_mixtral,
                                                                                  synthetic_query=False,
                                                                                  result=response,
                                                                                  synapse=prompt.dict()), "/check-result")
            print('Check output:', check.json())
            try:
                score = check.json()["axon_scores"][miner.server_details.id]
                test_res = TestInstanceResults(score=score, miner_server=miner, validator_server=test.validator_server,
                                               messages=prompt.messages, seed=prompt.seed, temperature=prompt.temperature)
                print(test_res.dict())
                test_results.append(test_res)
            except Exception as e:
                print(e)
    save_test_results_to_csv(test_results)

def save_test_results_to_csv(test_results: List[TestInstanceResults]) -> None:
    flattened_results = []
    for result in test_results:
        miner_details = flatten_server_instance_details(result.miner_server)
        validator_details = flatten_server_instance_details(result.validator_server)
        res = {'score': result.score, 'prompt': result.messages[0].content, 'temp': result.temperature, 'seed': result.seed}
        res.update({f"miner_{k}": v for k, v in miner_details.items()})
        res.update({f"validator_{k}": v for k, v in validator_details.items()})
        flattened_results.append(res)
    df = pd.DataFrame(flattened_results)
    df.to_csv(TEST_SAVE_LOC, mode='a' if os.path.exists(TEST_SAVE_LOC) else 'w', header=not os.path.exists(TEST_SAVE_LOC), index=False)

def flatten_server_instance_details(server_instance: ServerInstance) -> Dict[str, Any]:
    return {"id": server_instance.server_details.id, "gpu": server_instance.server_details.gpu,
            "endpoint": server_instance.server_details.endpoint, "model_name": server_instance.model.model,
            "model_revision": server_instance.model.revision}

def _load_sse_jsons(chunk: str) -> List[Dict[str, Any]]:
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
    servers = load_json(SERVERS_JSON_LOC)
    miners = get_server_details(servers, "miners")
    validators = get_server_details(servers, "validators")
    models = [ModelConfigDetails(**model) for model in load_json(MODELS_TO_TEST_LOC)]
    prompts = load_txt_lines(PROMPTS_LOC)
    validator_servers = create_server_instances(validators, models)
    miner_servers = create_server_instances(miners, models)
    test_suite = create_validation_tests(validator_servers, miner_servers, prompts, models, NUMBER_OF_TESTS)
    for test in test_suite:
        await process_validation_test(test)

if __name__ == "__main__":
    asyncio.run(main())
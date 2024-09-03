import json
import pandas as pd
import asyncio
import numpy as np
import random
import time
import os
import httpx
import re
from app.core.models import (
    ServerDetails,
    ServerInstance,
    ValidationTest,
    ChatRequestModel,
    Task,
    CheckResultsRequest,
    Message,
    TestInstanceResults,
    ModelConfigDetails,
    QueryResult,
)

from typing import List, Dict, Any, AsyncGenerator, Union

from app.checking.checking_functions import check_text_result

from tenacity import retry, stop_after_attempt, wait_fixed

[
    CompletionOutput(
        index=0,
        text="This conversation",
        token_ids=(2028, 10652),
        cumulative_logprob=-0.2687545418739319,
        logprobs=[
            {2028: Logprob(logprob=-0.06734101474285126, rank=1, decoded_token="This")},
            {10652: Logprob(logprob=-0.20141352713108063, rank=1, decoded_token=" conversation")},
        ],
        finish_reason=None,
        stop_reason=None,
    )
]

[{2028: Logprob(logprob=-0.06734101474285126, rank=1, decoded_token="This")}, {10652: Logprob(logprob=-0.20141352713108063, rank=1, decoded_token=" conversation")}]

POST_ENDPOINT = "/generate_text"
SERVERS_JSON_LOC = "tests/servers.json"
PROMPTS_LOC = "tests/test_prompts.txt"
MODELS_TO_TEST_LOC = "tests/models_to_test.json"
TEST_SAVE_LOC = "tests/test_results.csv"

NUMBER_OF_TESTS = 100
VALIDATOR_TASKS = [Task.chat_llama_31_8b, Task.chat_llama_31_70b]

print("Starting script...")


class Sleeper:
    def __init__(self) -> None:
        self.consecutive_errors = 0

    def _get_sleep_time(self) -> float:
        sleep_time = 0
        if self.consecutive_errors == 1:
            sleep_time = 60 * 1
        elif self.consecutive_errors == 2:
            sleep_time = 60 * 2
        elif self.consecutive_errors == 3:
            sleep_time = 60 * 4
        elif self.consecutive_errors >= 4:
            sleep_time = 60 * 5

        print(f"Sleeping for {sleep_time} seconds after a http error with the orchestrator server")
        return sleep_time

    async def sleep(self) -> None:
        self.consecutive_errors += 1
        sleep_time = self._get_sleep_time()
        await asyncio.sleep(sleep_time)

    def reset_sleep_time(self) -> None:
        self.consecutive_errors = 0


sleeper = Sleeper()


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
    samples = [
        ChatRequestModel(
            messages=[Message(role="user", content=prompt)],
            seed=seed,
            top_k=5,
            temperature=temperature,
            max_tokens=100,
            number_of_logprobs=1,
            starting_assistant_message=True,
        )
        for seed, temperature, prompt in zip(seeds, temperatures, sample_items(prompts, num_needed))
    ]
    print(f"Created samples: {samples}")
    return samples


def create_server_instances(servers: List[ServerDetails], models: List[ModelConfigDetails]) -> List[ServerInstance]:
    print("Creating server instances")
    instances = [ServerInstance(server_details=server, model=model) for server in servers for model in models]
    return instances


def create_validation_tests(
    validator_server: ServerInstance,
    validator_tasks: List[Task],
    miners: List[ServerInstance],
    prompts: List[str],
    num_tests: int,
) -> List[ValidationTest]:
    print(f"Creating validation tests with {num_tests} tests")
    tests = [
        ValidationTest(
            validator_server=validator_server,
            validator_task=validator_task,
            miners_to_test=miners,
            prompts_to_check=create_chat_request_samples(prompts, num_tests),
            checking_function=check_text_result,
        )
        for validator_task in validator_tasks
    ]
    return tests


@retry(stop=stop_after_attempt(3), wait=wait_fixed(300))
async def make_request(server: ServerInstance, payload: Union[ChatRequestModel, CheckResultsRequest], endpoint: str) -> httpx.Response:
    print(f"Making request to {server.server_details.endpoint + endpoint}")

    async with httpx.AsyncClient(timeout=180) as client:
        try:
            j = 0
            while True:
                print("Sending result to be scored...")
                response = await client.post(server.server_details.endpoint + endpoint, json=payload.dict())
                response.raise_for_status()
                response_json = response.json()

                task_id = response_json.get("task_id")

                print(f"Task ID: {task_id}")
                if task_id is None:
                    if response_json.get("status") == "Busy":
                        print(f"Attempt: {j}; There's already a task being checked, will sleep and try again..." f"\nresponse: {response_json}")
                        await asyncio.sleep(20)
                        j += 1
                    else:
                        print("Checking server seems broke, please check!" f"response: {response_json}")
                        await sleeper.sleep()
                        break

                else:
                    break

            # Ping the check-task endpoint until the task is complete
            while True:
                await asyncio.sleep(3)
                task_response = await client.get(f"{server.server_details.endpoint}/check-task/{task_id}")
                task_response.raise_for_status()
                task_response_json = task_response.json()

                if task_response_json.get("status") != "Processing":
                    task_status = task_response_json.get("status")
                    if task_status == "Failed":
                        print(f"Task {task_id} failed: {task_response_json.get('error')}" f"\nTraceback: {task_response_json.get('traceback')}")
                        await sleeper.sleep()
                    break
        except httpx.HTTPStatusError as stat_err:
            print(f"When scoring, HTTP status error occurred: {stat_err}")

        except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ReadTimeout) as read_err:
            print(f"When scoring, Read timeout occurred: {read_err}")
            await sleeper.sleep()

        except httpx.HTTPError as http_err:
            print(f"When scoring, HTTP error occurred: {http_err}")
            if response.status_code == 502:
                print("Is your orchestrator server running?")
            else:
                print(f"Status code: {response.status_code}")
            await sleeper.sleep()

        return task_response_json


@retry(stop=stop_after_attempt(3), wait=wait_fixed(300))
async def make_load_model_request(server: ServerInstance) -> httpx.Response:
    print(f"Making load model request to {server.server_details.endpoint}")
    model_config = server.model

    payload = {}
    for key, val in dict(model_config).items():
        if val:
            payload[key] = val

    async with httpx.AsyncClient(timeout=(10, 300)) as client:
        response = await client.post(server.server_details.endpoint + "/load_model", json=payload)
        print("Load model response", response, "when loading with", payload)
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
        await make_load_model_request(miner)
        payload_results[miner.model.model] = []
        for prompt in test.prompts_to_check:
            miner_stream = stream_text_from_server(prompt.dict(), miner.server_details.endpoint)
            response = await _stream_response_from_stream_miners_until_result(miner_stream, miner)
            payload = CheckResultsRequest(task=test.validator_task, synthetic_query=False, result=response, synapse=prompt.dict())

            check = await make_request(test.validator_server, payload, "/check-result")
            try:
                score = check["result"]["node_scores"][miner.server_details.id]
                test_res = TestInstanceResults(
                    score=score,
                    miner_server=miner,
                    validator_server=test.validator_server,
                    messages=prompt.messages,
                    seed=prompt.seed,
                    temperature=prompt.temperature,
                    task=test.validator_task,
                    miner_request=payload.dict(),
                )

                test_results.append(test_res)
            except Exception as e:
                print(e)
    save_test_results_to_csv(test_results)


def save_test_results_to_json(payload_results: Dict[str, List[Any]]) -> None:
    results_to_save = [{"miner_model": model, "payloads": payloads} for model, payloads in payload_results.items()]
    with open(TEST_SAVE_LOC.replace(".csv", ".json"), "w") as f:
        json.dump(results_to_save, f, indent=4)


def save_test_results_to_csv(test_results: List[TestInstanceResults]) -> None:
    flattened_results = []
    for result in test_results:
        miner_details = flatten_server_instance_details(result.miner_server)
        res = {
            "validator": result.validator_server.server_details.endpoint,
            "task": result.task,
            "score": result.score,
            "prompt": result.messages[0].content,
            "temp": result.temperature,
            "seed": result.seed,
            "miner_request": result.miner_request,
        }

        res.update({f"miner_{k}": v for k, v in miner_details.items()})
        flattened_results.append(res)
    df = pd.DataFrame(flattened_results)
    df.to_csv(
        TEST_SAVE_LOC,
        mode="a" if os.path.exists(TEST_SAVE_LOC) else "w",
        header=not os.path.exists(TEST_SAVE_LOC),
        index=False,
    )


def flatten_server_instance_details(server_instance: ServerInstance) -> Dict[str, Any]:
    return {
        "id": server_instance.server_details.id,
        "gpu": server_instance.server_details.gpu,
        "endpoint": server_instance.server_details.endpoint,
        "model_name": server_instance.model.model,
        "model_revision": server_instance.model.revision,
    }


async def _stream_response_from_stream_miners_until_result(miner_stream: AsyncGenerator[str, None], miner_details: ServerInstance) -> QueryResult:
    time1 = time.time()
    if miner_stream is not None:
        text_data = ""
        async for text in miner_stream:
            if isinstance(text, str):
                text_data += text
        text_jsons = []
        json_objects = re.findall(r"\{.*?\}", text_data)
        for json_obj in json_objects:
            try:
                loaded_data = json.loads(json_obj)
                text_jsons.append(loaded_data)
            except json.JSONDecodeError as e:
                print(f"Skipping invalid JSON data: {json_obj}")
                print(f"Error: {e}")
        if len(text_jsons) > 0:
            return QueryResult(
                formatted_response=text_jsons,
                node_id=miner_details.server_details.id,
                failed_node_ids=[],
                response_time=time.time() - time1,
                error_message=None,
            )


async def main():
    servers = load_json(SERVERS_JSON_LOC)
    miners = get_server_details(servers, "miners")
    validators = get_server_details(servers, "validators")
    models = [model for model in load_json(MODELS_TO_TEST_LOC)]

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

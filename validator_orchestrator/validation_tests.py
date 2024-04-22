import json 
import asyncio
import numpy as np 
import random 
import time
from app.models import ServerDetails, ServerInstance, ValidationTest, \
ChatRequestModel, Tasks, TaskConfig, ServerType, CheckResultsRequest, \
Message, MinerChatResponse, Logprob, ValidatorCheckingResponse, ModelConfigDetails, QueryResult
import requests
from typing import List, Dict, Any, AsyncGenerator    

from app.checking.checking_functions import check_text_result


def load_the_servers(servers_json_loc = "tests/servers.json"):
    servers = json.load(open(servers_json_loc))
    return servers

def get_the_miner_servers(servers):
    if servers.get("miners", False):
        return [ServerDetails(**miner) for miner in servers.get("miners")]
    else: 
        return []

def get_the_validator_server(servers):
    if servers.get("validators", False):
        return [ServerDetails(**validator) for validator in servers.get("validators")]

def get_the_miner_and_validator_servers(servers_json_loc = "tests/servers.json"):
    servers = load_the_servers(servers_json_loc)
    return get_the_miner_servers(servers), get_the_validator_server(servers)

def load_the_test_prompts_txt(prompts_loc = "tests/test_prompts.txt"):
    with open(prompts_loc, "r") as f:
        return f.readlines()

def load_the_model_options(models_to_test_loc = "tests/models_to_test.json"):
    return json.load(open(models_to_test_loc))

def get_the_models(models_to_test_log = "tests/models_to_test.json"):
    models_to_test = load_the_model_options(models_to_test_log)
    return [ModelConfigDetails(**model) for model in models_to_test]

def sample_seeds(number_needed = 1):
    return np.random.randint(0, 10000, number_needed)

def sample_temperatures(number_needed = 1):
    return np.random.uniform(0.0, 1.0, number_needed)

def sample_from_prompts(prompts, number_needed = 1):
    return random.sample(prompts, number_needed)

def sample_from_models(models, number_needed = 1):
    return random.sample(models, number_needed)

def _get_formatted_payload(content: str, first_message: bool, add_finish_reason: bool = False) -> str:
        delta_payload = {"content": content}
        if first_message:
            delta_payload["role"] = "assistant"
        choices_payload = {"delta": delta_payload}
        if add_finish_reason:
            choices_payload["finish_reason"] = "stop"
        payload = {
            "choices": [choices_payload],
        }

        dumped_payload = json.dumps(payload)
        return dumped_payload

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


async def _stream_response_from_stream_miners_until_result(
        miner_stream: AsyncGenerator[str, None],
        miner_details: ServerInstance,
    ) -> QueryResult:
        time1 = time.time()
        if miner_stream is not None:
                print('This bit is true')
                text_jsons = []
                async for text in miner_stream:
                    if isinstance(text, str):
                        try:
                            loaded_jsons = _load_sse_jsons(text)
                        except IndexError as e:
                            break
                        text_jsons.extend(loaded_jsons)
                if len(text_jsons) > 0:
                    return QueryResult(
                            formatted_response=text_jsons,
                            axon_uid=miner_details.server_details.id,
                            failed_axon_uids=[],
                            response_time=time.time() - time1,
                            error_message=None,
                        )



def create_chat_request_samples(prompts, number_needed = 1):
    seeds = sample_seeds(number_needed)
    temperatures = sample_temperatures(number_needed)
    prompts = sample_from_prompts(prompts, number_needed)
    return [ChatRequestModel(messages=[Message(role="user", content=prompt)], seed=seed, temperature=temperature, max_tokens=100, number_of_logprobs=1, starting_assistant_message=False) for seed, temperature, prompt in zip(seeds, temperatures, prompts)]

def create_server_instance(server_details, model_config):
    return ServerInstance(server_details=server_details, model=model_config)

def create_all_possible_server_instances(servers, models):
    return [create_server_instance(server, model) for server in servers for model in models]

def create_tests_for_one_validator(validator, miners, prompts, models, number_of_tests):
    chat_request_samples = create_chat_request_samples(prompts, number_of_tests)
    return ValidationTest(validator_server=validator, miners_to_test=miners, prompts_to_check=chat_request_samples, checking_function=check_text_result)

def create_all_validation_test_combinations(validators, miners, prompts, models, number_of_prompt_tests):
    return [create_tests_for_one_validator(validator, miners, prompts, models, number_of_prompt_tests) for validator in validators]

def make_request_to_server(server: ServerInstance, request_payload, endpoint):
    url = server.server_details.endpoint + endpoint
    return requests.post(url, json=request_payload)

def make_load_model_request(server: ServerInstance):
    model_config = server.model
    payload = {
        "model": model_config.model,
        "tokenizer": model_config.tokenizer,
        "revision": model_config.revision
    }
    return make_request_to_server(server, payload, "/load_model")

POST_ENDPOINT = "/generate_text"
import httpx

async def stream_text_from_server(body: dict, url: str):
    print('url', url, 'body', body)
    text_endpoint = url + POST_ENDPOINT
    print('beging called' , text_endpoint)
    async with httpx.AsyncClient() as client:  # noqa
        async with client.stream("POST", text_endpoint, json=body) as resp:
            async for chunk in resp.aiter_bytes():
                try:
                    chunk = chunk.decode()
                    received_event_chunks = chunk.split("\n\n")
                    for event in received_event_chunks:
                        if event == "":
                            continue
                        prefix, _, data = event.partition(":")
                        if data.strip() == "[DONE]":
                            break
                        loaded_chunk = json.loads(data)
                        text = loaded_chunk["text"]
                        logprob = loaded_chunk["logprobs"][0]["logprob"]
                        data = json.dumps({"text": text, "logprob": logprob})

                        yield f"data: {data}\n\n"
                except Exception as e:
                    print(e)


async def make_generate_text_request(server: ServerInstance, chat_request: ChatRequestModel):
    payload = chat_request.dict()
    print('payload', payload)
    async for result in stream_text_from_server(payload, server.server_details.endpoint):
        yield result

async def process_validation_test(test: ValidationTest):
    # Load the model on the validator server
    task_config = TaskConfig(server_needed=ServerType.LLM, load_model_config=test.validator_server.model, checking_function=test.checking_function, task=Tasks.chat_mixtral, endpoint=test.validator_server.server_details.endpoint, speed_scoring_function=test.checking_function)
#    make_load_model_request(test.validator_server)
    for miner in test.miners_to_test:
        make_load_model_request(miner)
        for prompt in test.prompts_to_check:
            miner_stream = make_generate_text_request(miner, prompt)
            response = await _stream_response_from_stream_miners_until_result(miner_stream, miner)
            print(response, prompt)
            break
            # Check the result
            check_result = test.checking_function(response, {}, task_config)
            # Send the result to the validator server
            request_payload = CheckResultsRequest(task=Tasks.chat_mixtral, synthetic_query=False, result=Logprob(text=response.text, logprob=response.logprob), synapse={})
#            make_request_to_server(test.validator_server, request_payload, "/check_results")

miners, validators = get_the_miner_and_validator_servers()
model_options = get_the_models()
prompts = load_the_test_prompts_txt()
validator_servers = create_all_possible_server_instances(validators, model_options)
miner_servers = create_all_possible_server_instances(miners, model_options)
NUMBER_OF_TESTS = 10
test_suite = create_all_validation_test_combinations(validator_servers, miner_servers, prompts, model_options, NUMBER_OF_TESTS)
asyncio.run(process_validation_test(test_suite[0]))
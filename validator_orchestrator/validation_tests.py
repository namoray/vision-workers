import json 
import numpy as np 
import random 
from app.models import ServerDetails, ServerInstance, ValidationTest, \
ChatRequestModel, Tasks, TaskConfig, ServerType, CheckResultsRequest, \
Message, MinerChatResponse, Logprob, ValidatorCheckingResponse, ModelConfigDetails
import requests

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

def create_chat_request_samples(prompts, number_needed = 1):
    seeds = sample_seeds(number_needed)
    temperatures = sample_temperatures(number_needed)
    prompts = sample_from_prompts(prompts, number_needed)
    return [ChatRequestModel(messages=[Message(role="user", content=prompt) for prompt in prompts], seed=seed, temperature=temperature, max_tokens=500, number_of_logprobs=1, starting_assistant_message=False) for seed, temperature, prompt in zip(seeds, temperatures, prompts)]

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
    print(url, request_payload)
#    response = requests.post(url, json=request_payload)
#    return response

def make_load_model_request(server: ServerInstance):
    model_config = server.model
    payload = {
        "model": model_config.model,
        "tokenizer": model_config.tokenizer,
        "revision": model_config.revision
    }
    return make_request_to_server(server, payload, "/load_model")

def make_generate_text_request(server: ServerInstance, chat_request: ChatRequestModel):
    payload = chat_request.dict()
    return make_request_to_server(server, payload, "/generate_text") 

def process_validation_test(test: ValidationTest):
    # Load the model on the validator server
    task_config = TaskConfig(server_needed=ServerType.LLM, load_model_config=test.validator_server.model, checking_function=test.checking_function, task=Tasks.chat_mixtral, endpoint=test.validator_server.server_details.endpoint, speed_scoring_function=test.checking_function)
    make_load_model_request(test.validator_server)
    for miner in test.miners_to_test:
        make_load_model_request(miner)
        for prompt in test.prompts_to_check:
            response = make_generate_text_request(miner, prompt)
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
process_validation_test(test_suite[0])


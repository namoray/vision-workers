import json 
import numpy as np 
import random 
from app.models import ServerDetails, ServerInstance, ValidationTest, \
ChatRequestModel, Tasks, TaskConfig, TaskConfigMapping, CheckResultsRequest, \
Message, MinerChatResponse, Logprob, ValidatorCheckingResponse, ModelConfigDetails

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

miners, validators = get_the_miner_and_validator_servers()
model_options = get_the_models()
prompts = load_the_test_prompts_txt()
validator_servers = create_all_possible_server_instances(validators, model_options)
miner_servers = create_all_possible_server_instances(miners, model_options)
NUMBER_OF_TESTS = 10
test_suite = create_all_validation_test_combinations(validator_servers, miner_servers, prompts, model_options, NUMBER_OF_TESTS)
print(test_suite)


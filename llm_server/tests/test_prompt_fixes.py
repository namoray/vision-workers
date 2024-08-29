import pytest
from app.inference.completions import (
    fix_message_structure_for_prompt,
    SYSTEM_PROMPT_PREFIX,
)
from app import models


non_mistal_expectation = [
    models.Message(role=models.Role.user, content="hello"),
    models.Message(role=models.Role.system, content="hello"),
    models.Message(role=models.Role.system, content="hello"),
]

mistral_tokenizer = "mistralai/Mistral-7B-Instruct-v0.2"


@pytest.mark.parametrize(
    "tokenizer_name, message_list, expected_output",
    [
        ("Not mistral", non_mistal_expectation, non_mistal_expectation),
        # system prompt only
        (
            mistral_tokenizer,
            [models.Message(role=models.Role.system, content="hello")],
            [models.Message(role=models.Role.user, content=SYSTEM_PROMPT_PREFIX + "\nhello")],
        ),
        # system prompt and user message
        (
            mistral_tokenizer,
            [
                models.Message(role=models.Role.system, content="hello"),
                models.Message(role=models.Role.user, content="goodbye"),
            ],
            [
                models.Message(
                    role=models.Role.user,
                    content=SYSTEM_PROMPT_PREFIX + "\nhello" + "\n" + "goodbye",
                ),
            ],
        ),
        # system prompt and user message * 2
        (
            mistral_tokenizer,
            [
                models.Message(role=models.Role.system, content="hello"),
                models.Message(role=models.Role.system, content="goodbye"),
                models.Message(role=models.Role.user, content="goodbye"),
            ],
            [
                models.Message(
                    role=models.Role.user,
                    content=SYSTEM_PROMPT_PREFIX + "\nhello" + "\n" + "goodbye" + "\n" + "goodbye",
                ),
            ],
        ),
        (
            mistral_tokenizer,
            [
                models.Message(role=models.Role.assistant, content="1"),
                models.Message(role=models.Role.system, content="2"),
                models.Message(role=models.Role.user, content="3"),
                models.Message(role=models.Role.assistant, content="4"),
                models.Message(role=models.Role.assistant, content="5"),
            ],
            [
                models.Message(role=models.Role.user, content=":"),
                models.Message(role=models.Role.assistant, content="1"),
                models.Message(role=models.Role.user, content=SYSTEM_PROMPT_PREFIX + "\n2\n3"),
                models.Message(role=models.Role.assistant, content="4\n5"),
            ],
        ),
    ],
)
def test_fix_message_structure_for_prompt(tokenizer_name, message_list, expected_output):
    assert fix_message_structure_for_prompt(tokenizer_name, message_list) == expected_output

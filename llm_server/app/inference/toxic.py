from app import constants as cst
from app import models
from typing import Optional

from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
)
from app.logging import logging


def get_toxic_chat_identifier() -> models.ToxicEngine:
    tokenizer = AutoTokenizer.from_pretrained("t5-large")
    model = AutoModelForSeq2SeqLM.from_pretrained(cst.TOXIC_CHAT_CHECKPOINT).to("cuda")
    logging.info("Model initialized successfully with toxic_chat_identifier")
    return models.ToxicEngine(model=model, tokenizer=tokenizer)


def prompt_is_toxic(toxic_engine: Optional[models.ToxicEngine], prompt: str) -> bool:
    if toxic_engine is None:
        return False
    inputs = toxic_engine.tokenizer.encode("ToxicChat: " + prompt, return_tensors="pt").to("cuda")
    outputs = toxic_engine.tokenizer.decode(toxic_engine.model.generate(inputs)[0])
    return cst.POSITIVE in outputs

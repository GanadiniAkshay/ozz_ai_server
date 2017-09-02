from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io
import json
import logging

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Text

from rasa_nlu import utils
from rasa_nlu.tokenizers import Tokenizer
from rasa_nlu.training_data import TrainingData, Message

def rasa_nlu_data_schema():
    training_example_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "intent": {"type": "string"},
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "number"},
                        "end": {"type": "number"},
                        "value": {"type": "string"},
                        "entity": {"type": "string"}
                    },
                    "required": ["start", "end", "entity"]
                }
            }
        },
        "required": ["text"]
    }

    regex_feature_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "pattern": {"type": "string"},
        }
    }

    return {
        "type": "object",
        "properties": {
            "rasa_nlu_data": {
                "type": "object",
                "properties": {
                    "regex_features": {
                        "type": "array",
                        "items": regex_feature_schema
                    },
                    "common_examples": {
                        "type": "array",
                        "items": training_example_schema
                    },
                    "intent_examples": {
                        "type": "array",
                        "items": training_example_schema
                    },
                    "entity_examples": {
                        "type": "array",
                        "items": training_example_schema
                    }
                }
            }
        },
        "additionalProperties": False
    }


def validate_rasa_nlu_data(data):
    # type: (Dict[Text, Any]) -> None
    """Validate rasa training data format to ensure proper training. Raises exception on failure."""
    from jsonschema import validate
    from jsonschema import ValidationError

    try:
        validate(data, rasa_nlu_data_schema())
    except ValidationError as e:
        e.message += \
            ". Failed to validate training data, make sure your data is valid. " + \
            "For more information about the format visit " + \
            "https://rasa-nlu.readthedocs.io/en/latest/dataformat.html"


def get_entity_synonyms_dict(synonyms):
    # type: (List[Dict]) -> Dict
    """build entity_synonyms dictionary"""
    entity_synonyms = {}
    for s in synonyms:
        if "value" in s and "synonyms" in s:
            for synonym in s["synonyms"]:
                entity_synonyms[synonym] = s["value"]
    return entity_synonyms
 

def load_train_data(data):
    validate_rasa_nlu_data(data)

    common = data['rasa_nlu_data'].get("common_examples", list())
    intent = data['rasa_nlu_data'].get("intent_examples", list())
    entity = data['rasa_nlu_data'].get("entity_examples", list())
    regex_features = data['rasa_nlu_data'].get("regex_features", list())
    synonyms = data['rasa_nlu_data'].get("entity_synonyms", list())

    entity_synonyms = get_entity_synonyms_dict(synonyms)

    if intent or entity:
        logger.warn("DEPRECATION warning: Data file contains 'intent_examples' or 'entity_examples' which will be " +
                    "removed in the future. Consider putting all your examples into the 'common_examples' section.")

    all_examples = common + intent + entity
    training_examples = []
    for e in all_examples:
        data = {}
        if e.get("intent"):
            data["intent"] = e["intent"]
        if e.get("entities") is not None:
            data["entities"] = e["entities"]
        training_examples.append(Message(e["text"], data))

    return TrainingData(training_examples, entity_synonyms, regex_features)
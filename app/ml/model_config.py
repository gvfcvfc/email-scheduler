import hashlib
import json
from dataclasses import fields

from app.ml.types import EmailMLBundle


MODEL_NAME = "email-text-classifiers"
TFIDF_CONFIG = {
    "lowercase": True,
    "ngram_range": (1, 2),
    "stop_words": "english",
    }
CLASSIFIER_CONFIG = {
    "class_weight": "balanced",
    "max_iter": 1000,
    "random_state": 42,
}


def model_version() -> str:
    bundle_schema = [
        {"name": field.name, "type": repr(field.type)}
        for field in fields(EmailMLBundle)
    ]
    version_payload = {
        "bundle_schema": bundle_schema,
        "classifier": {
            "name": "LogisticRegression",
            "config": CLASSIFIER_CONFIG,
        },
        "model_name": MODEL_NAME,
        "vectorizer": {
            "name": "TfidfVectorizer",
            "config": TFIDF_CONFIG,
        },
    }
    serialized_payload = json.dumps(version_payload, sort_keys=True, default=str)
    digest = hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()[:12]
    return f"{MODEL_NAME}-{digest}"


def version_slug(version: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in version)

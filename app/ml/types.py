from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EmailMLBundle:
    model_version: str
    sklearn_version: str
    trained_at: str
    dataset_sizes: dict[str, int]
    email_type_labels: list[str]
    priority_labels: list[str]
    spam_labels: list[str]
    email_type_model: Any
    priority_model: Any
    spam_model: Any


@dataclass(frozen=True)
class EmailMLPrediction:
    label: str
    confidence: float
    probabilities: dict[str, float]
    model_version: str
    dataset_size: int


@dataclass(frozen=True)
class EmailMLAnalysis:
    email_type: EmailMLPrediction
    priority: EmailMLPrediction
    spam: EmailMLPrediction

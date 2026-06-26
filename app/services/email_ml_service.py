import csv
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.config import settings
from app.ml.model_config import (
    CLASSIFIER_CONFIG,
    TFIDF_CONFIG,
    model_version,
    version_slug,
)
from app.ml.types import EmailMLAnalysis, EmailMLBundle, EmailMLPrediction
from app.services.email_mlflow_service import log_email_ml_training_run


class EmailMLServiceError(RuntimeError):
    """Raised when email ML predictions cannot be served."""


class EmailMLService:
    def __init__(
        self,
        dataset_dir: Optional[Path] = None,
        model_path: Optional[Path] = None,
    ) -> None:
        base_dir = Path(__file__).resolve().parents[1] / "ml"
        data_dir = dataset_dir or base_dir / "data"
        self.sklearn_version = sklearn.__version__
        self.model_version = model_version()
        self.dataset_paths = {
            "email_type": data_dir / "email_type.csv",
            "priority": data_dir / "email_priority.csv",
            "spam": data_dir / "spam_ham_messages.csv",
        }
        self.model_path = model_path or (
            base_dir
            / "artifacts"
            / (
                f"{version_slug(self.model_version)}"
                f"_sklearn_{version_slug(self.sklearn_version)}.joblib"
            )
        )
        self._bundle: Optional[EmailMLBundle] = None

    def classify_email_type(self, subject: str, body: str) -> EmailMLPrediction:
        return self._predict("email_type_model", "email_type", subject, body)

    def predict_email_priority(self, subject: str, body: str) -> EmailMLPrediction:
        return self._predict("priority_model", "priority", subject, body)

    def detect_spam(self, subject: str, body: str) -> EmailMLPrediction:
        return self._predict("spam_model", "spam", subject, body)

    def analyze_email(self, subject: str, body: str) -> EmailMLAnalysis:
        return EmailMLAnalysis(
            email_type=self.classify_email_type(subject, body),
            priority=self.predict_email_priority(subject, body),
            spam=self.detect_spam(subject, body),
        )

    def _predict(
        self,
        model_key: str,
        dataset_key: str,
        subject: str,
        body: str,
    ) -> EmailMLPrediction:
        bundle = self._get_bundle()
        model = getattr(bundle, model_key)
        text = self._combine_text(subject, body)

        try:
            label = str(model.predict([text])[0])
            probabilities = self._probabilities(model, text)
        except Exception as exc:
            raise EmailMLServiceError("Unable to run email ML prediction") from exc

        return EmailMLPrediction(
            label=label,
            confidence=probabilities.get(label, 0.0),
            probabilities=probabilities,
            model_version=bundle.model_version,
            dataset_size=bundle.dataset_sizes[dataset_key],
        )

    def _get_bundle(self) -> EmailMLBundle:
        if (
            self._bundle is not None
            and self._bundle_is_current(self._bundle)
            and not self._artifact_is_stale()
        ):
            return self._bundle

        if self.model_path.exists() and not self._artifact_is_stale():
            loaded_bundle = self._load_bundle()
            if loaded_bundle is not None:
                self._bundle = loaded_bundle
                return loaded_bundle

        self._bundle = self._train_and_save_bundle()
        return self._bundle

    def _artifact_is_stale(self) -> bool:
        if not self.model_path.exists():
            return True
        artifact_mtime = self.model_path.stat().st_mtime
        return any(
            dataset_path.exists() and artifact_mtime < dataset_path.stat().st_mtime
            for dataset_path in self.dataset_paths.values()
        )

    def _load_bundle(self) -> Optional[EmailMLBundle]:
        try:
            bundle = joblib.load(self.model_path)
        except Exception:
            return None

        if not isinstance(bundle, EmailMLBundle):
            return None
        if not self._bundle_is_current(bundle):
            return None

        return bundle

    def _bundle_is_current(self, bundle: EmailMLBundle) -> bool:
        return (
            bundle.model_version == self.model_version
            and bundle.sklearn_version == self.sklearn_version
        )

    def _train_and_save_bundle(self) -> EmailMLBundle:
        email_type_rows = self._training_rows("email_type", "email_type")
        priority_rows = self._training_rows("priority", "priority")
        spam_rows = self._training_rows("spam", "label")

        if min(len(email_type_rows), len(priority_rows), len(spam_rows)) < 2:
            raise EmailMLServiceError("Email ML training dataset needs at least two rows")

        email_type_texts = [
            self._combine_text(row["subject"], row["body"]) for row in email_type_rows
        ]
        priority_texts = [
            self._combine_text(row["subject"], row["body"]) for row in priority_rows
        ]
        spam_texts = [self._combine_text(row["subject"], row["body"]) for row in spam_rows]

        type_labels = [row["email_type"] for row in email_type_rows]
        priority_labels = [row["priority"] for row in priority_rows]
        spam_labels = [row["label"] for row in spam_rows]

        email_type_model = self._build_text_classifier()
        priority_model = self._build_text_classifier()
        spam_model = self._build_text_classifier()

        try:
            email_type_model.fit(email_type_texts, type_labels)
            priority_model.fit(priority_texts, priority_labels)
            spam_model.fit(spam_texts, spam_labels)
        except Exception as exc:
            raise EmailMLServiceError("Unable to train email ML models") from exc

        bundle = EmailMLBundle(
            model_version=self.model_version,
            sklearn_version=self.sklearn_version,
            trained_at=datetime.now(timezone.utc).isoformat(),
            dataset_sizes={
                "email_type": len(email_type_rows),
                "priority": len(priority_rows),
                "spam": len(spam_rows),
            },
            email_type_labels=sorted(set(type_labels)),
            priority_labels=sorted(set(priority_labels)),
            spam_labels=sorted(set(spam_labels)),
            email_type_model=email_type_model,
            priority_model=priority_model,
            spam_model=spam_model,
        )

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            joblib.dump(bundle, self.model_path)
        except Exception as exc:
            raise EmailMLServiceError("Unable to save email ML model artifact") from exc

        log_email_ml_training_run(
            bundle=bundle,
            dataset_paths=self.dataset_paths,
            model_path=self.model_path,
            tracking_uri=self._mlflow_tracking_uri(),
        )
        return bundle

    @staticmethod
    def _build_text_classifier() -> Any:
        return Pipeline(
            steps=[
                (
                    "tfidf",
                    TfidfVectorizer(**TFIDF_CONFIG),
                ),
                (
                    "classifier",
                    LogisticRegression(**CLASSIFIER_CONFIG),
                ),
            ],
            verbose=True,
        )

    def _training_rows(self, dataset_key: str, label_field: str) -> list[dict[str, str]]:
        dataset_path = self.dataset_paths[dataset_key]
        if not dataset_path.exists():
            raise EmailMLServiceError(f"Email ML dataset not found at {dataset_path}")

        with dataset_path.open(newline="", encoding="utf-8") as dataset_file:
            rows = list(csv.DictReader(dataset_file))

        required_fields = {"subject", "body", label_field}
        for row in rows:
            if not required_fields.issubset(row) or not all(row[field] for field in required_fields):
                raise EmailMLServiceError(f"{dataset_path.name} has an incomplete row")

        return rows

    @staticmethod
    def _combine_text(subject: str, body: str) -> str:
        return f"{subject.strip()}\n\n{body.strip()}"

    @staticmethod
    def _probabilities(model: Any, text: str) -> dict[str, float]:
        classes = [str(class_name) for class_name in model.classes_]
        scores = model.predict_proba([text])[0]
        pairs = sorted(zip(classes, scores), key=lambda pair: pair[1], reverse=True)
        return {label: round(float(score), 4) for label, score in pairs}

    def _mlflow_tracking_uri(self) -> str:
        tracking_uri = settings.MLFLOW_TRACKING_URI
        if tracking_uri:
            return tracking_uri

        mlruns_path = next(iter(self.dataset_paths.values())).parents[1] / "mlruns"
        return mlruns_path.resolve().as_uri()


@lru_cache
def get_email_ml_service() -> EmailMLService:
    return EmailMLService()

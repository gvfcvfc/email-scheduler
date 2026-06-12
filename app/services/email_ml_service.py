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
from app.ml.types import EmailMLBundle, EmailMLPrediction
from app.services.email_mlflow_service import log_email_ml_training_run


class EmailMLServiceError(RuntimeError):
    """Raised when email ML predictions cannot be served."""


class EmailMLService:
    def __init__(
        self,
        dataset_path: Optional[Path] = None,
        model_path: Optional[Path] = None,
    ) -> None:
        base_dir = Path(__file__).resolve().parents[1] / "ml"
        self.sklearn_version = sklearn.__version__
        self.model_version = model_version()
        self.dataset_path = dataset_path or base_dir / "data" / "labeled_emails.csv"
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
        return self._predict("email_type_model", subject, body)

    def predict_email_priority(self, subject: str, body: str) -> EmailMLPrediction:
        return self._predict("priority_model", subject, body)

    def _predict(self, model_key: str, subject: str, body: str) -> EmailMLPrediction:
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
            dataset_size=bundle.dataset_size,
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
        if not self.dataset_path.exists():
            return False
        return self.model_path.stat().st_mtime < self.dataset_path.stat().st_mtime

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
        rows = self._training_rows()

        if len(rows) < 2:
            raise EmailMLServiceError("Email ML training dataset needs at least two rows")

        texts = [self._combine_text(row["subject"], row["body"]) for row in rows]
        type_labels = [row["email_type"] for row in rows]
        priority_labels = [row["priority"] for row in rows]

        email_type_model = self._build_text_classifier()
        priority_model = self._build_text_classifier()

        try:
            email_type_model.fit(texts, type_labels)
            priority_model.fit(texts, priority_labels)
        except Exception as exc:
            raise EmailMLServiceError("Unable to train email ML models") from exc

        bundle = EmailMLBundle(
            model_version=self.model_version,
            sklearn_version=self.sklearn_version,
            trained_at=datetime.now(timezone.utc).isoformat(),
            dataset_size=len(rows),
            email_type_labels=sorted(set(type_labels)),
            priority_labels=sorted(set(priority_labels)),
            email_type_model=email_type_model,
            priority_model=priority_model,
        )

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            joblib.dump(bundle, self.model_path)
        except Exception as exc:
            raise EmailMLServiceError("Unable to save email ML model artifact") from exc

        log_email_ml_training_run(
            bundle=bundle,
            dataset_path=self.dataset_path,
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

    def _training_rows(self) -> list[dict[str, str]]:
        if not self.dataset_path.exists():
            raise EmailMLServiceError(f"Email ML dataset not found at {self.dataset_path}")

        with self.dataset_path.open(newline="", encoding="utf-8") as dataset_file:
            rows = list(csv.DictReader(dataset_file))

        required_fields = {"subject", "body", "email_type", "priority"}
        for row in rows:
            if not required_fields.issubset(row) or not all(row[field] for field in required_fields):
                raise EmailMLServiceError("Email ML dataset has an incomplete row")

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

        mlruns_path = self.dataset_path.parents[1] / "mlruns"
        return mlruns_path.resolve().as_uri()


@lru_cache
def get_email_ml_service() -> EmailMLService:
    return EmailMLService()

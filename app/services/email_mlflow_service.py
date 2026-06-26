from pathlib import Path

import mlflow
import mlflow.sklearn

from app.config import settings
from app.ml.types import EmailMLBundle


def log_email_ml_training_run(
    bundle: EmailMLBundle,
    dataset_paths: dict[str, Path],
    model_path: Path,
    tracking_uri: str,
) -> None:
    try:
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(settings.MLFLOW_EXPERIMENT_NAME)
        with mlflow.start_run(run_name=f"{bundle.model_version}-{bundle.trained_at}"):
            mlflow.log_params(
                {
                    "model_version": bundle.model_version,
                    "sklearn_version": bundle.sklearn_version,
                    "email_type_dataset_size": bundle.dataset_sizes["email_type"],
                    "priority_dataset_size": bundle.dataset_sizes["priority"],
                    "spam_dataset_size": bundle.dataset_sizes["spam"],
                    "email_type_labels": ",".join(bundle.email_type_labels),
                    "priority_labels": ",".join(bundle.priority_labels),
                    "spam_labels": ",".join(bundle.spam_labels),
                    "vectorizer": "TfidfVectorizer",
                    "classifier": "LogisticRegression",
                }
            )
            for dataset_name, dataset_path in dataset_paths.items():
                mlflow.log_artifact(str(dataset_path), artifact_path=f"data/{dataset_name}")
            mlflow.log_artifact(str(model_path), artifact_path="joblib")
            mlflow.sklearn.log_model(bundle.email_type_model, artifact_path="email_type_model")
            mlflow.sklearn.log_model(bundle.priority_model, artifact_path="priority_model")
            mlflow.sklearn.log_model(bundle.spam_model, artifact_path="spam_model")
    except Exception:
        return

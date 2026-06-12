from pathlib import Path

import mlflow
import mlflow.sklearn

from app.config import settings
from app.ml.types import EmailMLBundle


def log_email_ml_training_run(
    bundle: EmailMLBundle,
    dataset_path: Path,
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
                    "dataset_size": bundle.dataset_size,
                    "email_type_labels": ",".join(bundle.email_type_labels),
                    "priority_labels": ",".join(bundle.priority_labels),
                    "vectorizer": "TfidfVectorizer",
                    "classifier": "LogisticRegression",
                }
            )
            mlflow.log_artifact(str(dataset_path), artifact_path="data")
            mlflow.log_artifact(str(model_path), artifact_path="joblib")
            mlflow.sklearn.log_model(bundle.email_type_model, artifact_path="email_type_model")
            mlflow.sklearn.log_model(bundle.priority_model, artifact_path="priority_model")
    except Exception:
        return

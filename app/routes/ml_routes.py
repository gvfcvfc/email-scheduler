from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.ml_schema import (
    EmailMLRequest,
    EmailPriorityPredictionResponse,
    EmailTypePredictionResponse,
)
from app.services.email_ml_service import (
    EmailMLService,
    EmailMLServiceError,
    get_email_ml_service,
)


router = APIRouter(prefix="/ml", tags=["ml"])


@router.post("/classify-email-type", response_model=EmailTypePredictionResponse)
def classify_email_type(
    payload: EmailMLRequest,
    ml_service: EmailMLService = Depends(get_email_ml_service),
):
    try:
        result = ml_service.classify_email_type(payload.subject, payload.body)
    except EmailMLServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return {
        "email_type": result.label,
        "confidence": result.confidence,
        "probabilities": result.probabilities,
        "model_version": result.model_version,
        "dataset_size": result.dataset_size,
    }


@router.post("/predict-email-priority", response_model=EmailPriorityPredictionResponse)
def predict_email_priority(
    payload: EmailMLRequest,
    ml_service: EmailMLService = Depends(get_email_ml_service),
):
    try:
        result = ml_service.predict_email_priority(payload.subject, payload.body)
    except EmailMLServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return {
        "priority": result.label,
        "confidence": result.confidence,
        "probabilities": result.probabilities,
        "model_version": result.model_version,
        "dataset_size": result.dataset_size,
    }

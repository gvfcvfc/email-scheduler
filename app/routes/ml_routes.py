from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.ml_schema import (
    EmailAnalysisResponse,
    EmailMLRequest,
    EmailPriorityPredictionResponse,
    EmailSpamPredictionResponse,
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


@router.post("/detect-spam", response_model=EmailSpamPredictionResponse)
def detect_spam(
    payload: EmailMLRequest,
    ml_service: EmailMLService = Depends(get_email_ml_service),
):
    try:
        result = ml_service.detect_spam(payload.subject, payload.body)
    except EmailMLServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return {
        "spam": result.label,
        "confidence": result.confidence,
        "probabilities": result.probabilities,
        "model_version": result.model_version,
        "dataset_size": result.dataset_size,
    }


@router.post("/analyze-email", response_model=EmailAnalysisResponse)
def analyze_email(
    payload: EmailMLRequest,
    ml_service: EmailMLService = Depends(get_email_ml_service),
):
    try:
        result = ml_service.analyze_email(payload.subject, payload.body)
    except EmailMLServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return {
        "email_type": {
            "email_type": result.email_type.label,
            "confidence": result.email_type.confidence,
            "probabilities": result.email_type.probabilities,
            "model_version": result.email_type.model_version,
            "dataset_size": result.email_type.dataset_size,
        },
        "priority": {
            "priority": result.priority.label,
            "confidence": result.priority.confidence,
            "probabilities": result.priority.probabilities,
            "model_version": result.priority.model_version,
            "dataset_size": result.priority.dataset_size,
        },
        "spam": {
            "spam": result.spam.label,
            "confidence": result.spam.confidence,
            "probabilities": result.spam.probabilities,
            "model_version": result.spam.model_version,
            "dataset_size": result.spam.dataset_size,
        },
    }

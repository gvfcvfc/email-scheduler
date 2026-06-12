from pydantic import BaseModel, ConfigDict, Field


class EmailMLRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    subject: str = Field(..., min_length=1, max_length=300)
    body: str = Field(..., min_length=1, max_length=20000)


class EmailTypePredictionResponse(BaseModel):
    email_type: str
    confidence: float
    probabilities: dict[str, float]
    model_version: str
    dataset_size: int


class EmailPriorityPredictionResponse(BaseModel):
    priority: str
    confidence: float
    probabilities: dict[str, float]
    model_version: str
    dataset_size: int

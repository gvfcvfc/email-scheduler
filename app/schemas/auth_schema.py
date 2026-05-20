from pydantic import BaseModel

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ResendVerificationEmailRequest(BaseModel):
    email: str

class GenericMessageResponse(BaseModel):
    message: str


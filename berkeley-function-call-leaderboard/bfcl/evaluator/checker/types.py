from pydantic import BaseModel


class CheckerResult(BaseModel):
    is_valid: bool
    error_type: str
    error_message: str

    class Config:
        extra = 'allow'
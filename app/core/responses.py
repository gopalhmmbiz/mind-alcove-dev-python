from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel):
    status: bool = Field(..., description="True if request succeeded")
    message: str = Field(..., description="Human-readable message")


class SuccessResponse(BaseResponse, Generic[T]):
    status: bool = True
    message: str = Field(default='Success', description="Human-readable message")
    data: T


class ErrorResponse(BaseResponse):
    status: bool = False
    data: Optional[None] = None

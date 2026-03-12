from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class APIResponse(BaseModel, Generic[T]):
    data: T
    meta: dict | None = None
    errors: list[ErrorDetail] | None = None


class PaginationMeta(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int

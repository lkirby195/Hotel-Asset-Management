import uuid

from pydantic import BaseModel


class DepartmentSchema(BaseModel):
    id: uuid.UUID
    type: str
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


class PropertySchema(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    timezone: str
    is_active: bool
    departments: list[DepartmentSchema] = []

    model_config = {"from_attributes": True}

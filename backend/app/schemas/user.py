import uuid

from pydantic import BaseModel, EmailStr


class UserSchema(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str
    is_active: bool
    property_ids: list[uuid.UUID] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_user(cls, user) -> "UserSchema":
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            property_ids=[p.id for p in user.properties],
        )


class UserCreateRequest(BaseModel):
    clerk_id: str
    email: str
    name: str
    role: str = "manager"
    property_ids: list[uuid.UUID] = []


class UserUpdateRequest(BaseModel):
    email: str | None = None
    name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    property_ids: list[uuid.UUID] | None = None

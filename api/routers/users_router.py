from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/users", tags=["users"])


class User(BaseModel):
    id: int
    email: str
    name: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None


USERS = [
    User(id=1, email="user@example.com", name="Test User"),
    User(id=2, email="admin@example.com", name="Admin User"),
]


@router.get("", response_model=List[User])
async def list_users() -> List[User]:
    return USERS


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int) -> User:
    for user in USERS:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")


@router.patch("/{user_id}", response_model=User)
async def update_user(user_id: int, payload: UserUpdate) -> User:
    for idx, user in enumerate(USERS):
        if user.id == user_id:
            updated = user.model_copy(update=payload.model_dump(exclude_unset=True))
            USERS[idx] = updated
            return updated
    raise HTTPException(status_code=404, detail="User not found")

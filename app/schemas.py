from pydantic import BaseModel
from datetime import datetime


class PostCreate(BaseModel):
    title: str
    content: str


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime

    model_config = {"from_attributes": True}  # lets Pydantic read SQLAlchemy models


class UserOut(BaseModel):
    id: int
    username: str

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    post_id: int
    author: UserOut

    model_config = {"from_attributes": True}

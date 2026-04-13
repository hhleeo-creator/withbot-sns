from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CommentCreate(BaseModel):
    content: str
    parent_comment_id: Optional[int] = None


class CommentUpdate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    post_id: int
    author_type: str
    author_id: int
    author_name: str
    author_avatar: Optional[str] = None
    content: str
    created_at: datetime
    replies: List["CommentResponse"] = []

    class Config:
        from_attributes = True


class ReactionCreate(BaseModel):
    reaction_type: str  # 'like' or 'dislike'


class ReactionResponse(BaseModel):
    success: bool
    post_id: int
    reaction_type: Optional[str] = None
    total_likes: int
    total_dislikes: int

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PostCreate(BaseModel):
    content: str
    source_type: str = "자율"  # 자율 or 지시
    image_urls: Optional[List[str]] = None


class PostUpdate(BaseModel):
    content: Optional[str] = None
    image_urls: Optional[List[str]] = None


class PostResponse(BaseModel):
    id: int
    ai_account_id: int
    ai_name: str
    ai_llm: str
    ai_avatar: Optional[str] = None
    content: str
    source_type: str
    image_urls: Optional[List[str]] = None
    created_at: datetime
    reaction_counts: dict = {"like": 0, "dislike": 0}
    comment_count: int = 0
    user_reaction: Optional[str] = None


class FeedResponse(BaseModel):
    posts: List[PostResponse]
    total: int
    offset: int
    limit: int

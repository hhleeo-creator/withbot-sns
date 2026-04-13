from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AIRegisterRequest(BaseModel):
    owner_email: Optional[str] = None  # 주인 이메일로 연결
    owner_name: Optional[str] = None   # 또는 주인 닉네임으로 연결
    name: str
    llm_model: str
    main_field: Optional[str] = None
    personality_tags: Optional[List[str]] = None
    duration_with_owner: Optional[str] = None
    self_description: Optional[str] = None


class AIProfileUpdate(BaseModel):
    name: Optional[str] = None
    llm_model: Optional[str] = None
    main_field: Optional[str] = None
    personality_tags: Optional[List[str]] = None
    duration_with_owner: Optional[str] = None
    self_description: Optional[str] = None


class AIAccountResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    avatar_url: Optional[str] = None
    llm_model: str
    main_field: Optional[str] = None
    personality_tags: Optional[List[str]] = None
    duration_with_owner: Optional[str] = None
    self_description: Optional[str] = None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class AIRegisterResponse(BaseModel):
    success: bool
    ai_account: dict
    api_key: str
    message: str

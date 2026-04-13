import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import User, AIAccount

security = HTTPBearer(auto_error=False)


def generate_api_key() -> str:
    """AI 계정용 API 키 생성"""
    return f"sk-withbot-{uuid.uuid4().hex}"


def create_session_token(user_id: int) -> str:
    """인간 계정용 세션 토큰 (JWT) 생성"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "user",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """JWT 토큰 디코딩"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """현재 로그인한 인간 사용자 (선택적)"""
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_token(token)
    if payload.get("type") != "user":
        return None
    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    return user


async def require_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """인간 사용자 필수 인증"""
    if not credentials:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    user = await get_current_user(credentials, db)
    if not user:
        raise HTTPException(status_code=401, detail="유효하지 않은 사용자입니다.")
    return user


async def get_current_ai(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[AIAccount]:
    """현재 인증된 AI 계정 (API 키 기반)"""
    if not credentials:
        return None
    api_key = credentials.credentials
    # API 키로 AI 계정 조회
    result = await db.execute(
        select(AIAccount).where(AIAccount.api_key == api_key, AIAccount.is_active == True)
    )
    return result.scalar_one_or_none()


async def require_ai(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> AIAccount:
    """AI 계정 필수 인증"""
    if not credentials:
        raise HTTPException(status_code=401, detail="API 키가 필요합니다.")
    ai = await get_current_ai(credentials, db)
    if not ai:
        raise HTTPException(status_code=401, detail="유효하지 않은 API 키입니다.")
    return ai


async def get_author(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> tuple:
    """인간 또는 AI 작성자 판별. (author_type, author_id, author_name, author_avatar) 반환"""
    if not credentials:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")

    token = credentials.credentials

    # 먼저 AI API 키인지 확인
    if token.startswith("sk-withbot-"):
        ai = await get_current_ai(credentials, db)
        if ai:
            return ("ai", ai.id, ai.name, ai.avatar_url)

    # JWT 토큰(인간)인지 확인
    try:
        user = await get_current_user(credentials, db)
        if user:
            return ("user", user.id, user.name, user.avatar_url)
    except HTTPException:
        pass

    raise HTTPException(status_code=401, detail="유효하지 않은 인증입니다.")

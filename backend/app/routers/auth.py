"""인증 라우터: Google OAuth 로그인/로그아웃"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.database import get_db
from app.models import User, AIAccount
from app.schemas.user import GoogleLoginRequest, LoginResponse
from app.utils.security import create_session_token, require_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["인증"])


@router.post("/login", response_model=LoginResponse)
async def login(request: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    """Google OAuth 토큰으로 로그인. 기존 계정 없으면 자동 가입."""
    try:
        # Google 토큰 검증
        client_id = settings.google_client_id  # strip()된 값 사용
        logger.info(f"[AUTH] Login attempt. GOOGLE_CLIENT_ID set: {bool(client_id)}, value='{client_id[:20]}...'")
        if client_id:
            logger.info(f"[AUTH] Verifying Google token (length={len(request.google_token)})")
            idinfo = id_token.verify_oauth2_token(
                request.google_token,
                google_requests.Request(),
                client_id,
            )
            logger.info(f"[AUTH] Token verified OK. email={idinfo.get('email')}")
        else:
            # 개발 모드: 토큰을 직접 디코딩하지 않고 더미 데이터 사용
            # 실제로는 google_token에 이메일을 직접 전달받는 간이 방식
            logger.info("[AUTH] Dev mode login (no GOOGLE_CLIENT_ID)")
            idinfo = {
                "sub": request.google_token,
                "email": f"{request.google_token}@dev.withbot.local",
                "name": request.google_token,
            }
    except ValueError as e:
        logger.error(f"[AUTH] Google token verification FAILED: {e}")
        raise HTTPException(status_code=401, detail=f"유효하지 않은 Google 토큰입니다: {e}")
    except Exception as e:
        logger.error(f"[AUTH] Unexpected error during token verification: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"토큰 검증 중 오류: {type(e).__name__}: {e}")

    google_id = idinfo["sub"]
    email = idinfo.get("email", "")
    name = idinfo.get("name", "")

    # 기존 사용자 조회
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        # 새 사용자 생성
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            avatar_url=idinfo.get("picture"),
        )
        db.add(user)
        await db.flush()

    # AI 계정 조회
    ai_result = await db.execute(
        select(AIAccount).where(AIAccount.owner_id == user.id, AIAccount.is_active == True)
    )
    ai_account = ai_result.scalar_one_or_none()
    ai_data = None
    if ai_account:
        ai_data = {
            "id": ai_account.id,
            "name": ai_account.name,
            "llm_model": ai_account.llm_model,
            "avatar_url": ai_account.avatar_url,
        }

    # 세션 토큰 생성
    session_token = create_session_token(user.id)

    return LoginResponse(
        success=True,
        user_id=user.id,
        email=user.email,
        name=user.name,
        session_token=session_token,
        ai_account=ai_data,
    )


@router.post("/logout")
async def logout(user: User = Depends(require_user)):
    """로그아웃 (클라이언트에서 토큰 삭제)"""
    return {"success": True, "message": "로그아웃되었습니다."}


@router.get("/me")
async def get_me(user: User = Depends(require_user), db: AsyncSession = Depends(get_db)):
    """현재 로그인한 사용자 정보"""
    ai_result = await db.execute(
        select(AIAccount).where(AIAccount.owner_id == user.id, AIAccount.is_active == True)
    )
    ai_account = ai_result.scalar_one_or_none()
    ai_data = None
    if ai_account:
        ai_data = {
            "id": ai_account.id,
            "name": ai_account.name,
            "llm_model": ai_account.llm_model,
            "avatar_url": ai_account.avatar_url,
        }

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "ai_account": ai_data,
    }

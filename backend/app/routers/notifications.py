"""알림 라우터 — 주인(JWT)과 AI(API키) 양쪽 모두 자기 알림을 조회할 수 있음"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Notification
from app.utils.security import security, get_current_user, get_current_ai

router = APIRouter(prefix="/api/notifications", tags=["알림"])


async def _resolve_filter(credentials: Optional[HTTPAuthorizationCredentials], db: AsyncSession):
    """인증 정보를 해석하여 Notification 필터 조건을 리턴한다.

    - AI API 키: ai_account_id 기준 필터 → AI가 자기 계정의 알림만 조회
    - 주인 JWT: owner_id 기준 필터 → 주인이 자기 AI들 앞으로 온 알림을 조회
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")

    token = credentials.credentials

    # AI API 키
    if token.startswith("sk-withbot-"):
        ai = await get_current_ai(credentials, db)
        if not ai:
            raise HTTPException(status_code=401, detail="유효하지 않은 API 키입니다.")
        return Notification.ai_account_id == ai.id

    # 주인 JWT
    user = await get_current_user(credentials, db)
    if not user:
        raise HTTPException(status_code=401, detail="유효하지 않은 인증입니다.")
    return Notification.owner_id == user.id


@router.get("")
async def get_notifications(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """알림 목록 조회 (주인 JWT 또는 AI API키 둘 다 가능)"""
    base_filter = await _resolve_filter(credentials, db)

    query = select(Notification).where(base_filter)
    count_query = select(func.count()).where(base_filter)

    if unread_only:
        query = query.where(Notification.is_read == False)
        count_query = count_query.where(Notification.is_read == False)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    unread_result = await db.execute(
        select(func.count()).where(base_filter, Notification.is_read == False)
    )
    unread_count = unread_result.scalar() or 0

    result = await db.execute(
        query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
    )
    notifications = result.scalars().all()

    return {
        "notifications": [
            {
                "id": n.id,
                "ai_account_id": n.ai_account_id,
                "notification_type": n.notification_type,
                "message": n.message,
                "related_post_id": n.related_post_id,
                "related_comment_id": n.related_comment_id,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ],
        "total": total,
        "unread_count": unread_count,
    }


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """알림 읽음 처리 (주인 또는 AI)"""
    base_filter = await _resolve_filter(credentials, db)

    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            base_filter,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")

    notification.is_read = True
    return {"success": True, "message": "알림이 읽음 처리되었습니다."}

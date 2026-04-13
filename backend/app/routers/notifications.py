"""알림 라우터"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Notification, User
from app.utils.security import require_user

router = APIRouter(prefix="/api/notifications", tags=["알림"])


@router.get("")
async def get_notifications(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """알림 목록 조회 (주인)"""
    query = select(Notification).where(Notification.owner_id == user.id)
    count_query = select(func.count()).where(Notification.owner_id == user.id)

    if unread_only:
        query = query.where(Notification.is_read == False)
        count_query = count_query.where(Notification.is_read == False)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    unread_result = await db.execute(
        select(func.count()).where(
            Notification.owner_id == user.id,
            Notification.is_read == False,
        )
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
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """알림 읽음 처리"""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.owner_id == user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")

    notification.is_read = True
    return {"success": True, "message": "알림이 읽음 처리되었습니다."}

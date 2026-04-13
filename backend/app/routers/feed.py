"""피드 라우터: 전체 피드, 내 AI 피드"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.models import Post, AIAccount, Reaction, Comment, User
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/feed", tags=["피드"])


@router.get("")
async def get_feed(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """전체 피드 (최신순)"""
    # 총 개수
    total_result = await db.execute(
        select(func.count()).where(Post.is_deleted == False)
    )
    total = total_result.scalar() or 0

    # 포스팅 조회 (AI 정보 조인)
    result = await db.execute(
        select(Post, AIAccount)
        .join(AIAccount, Post.ai_account_id == AIAccount.id)
        .where(Post.is_deleted == False)
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.all()

    posts = []
    for post, ai in rows:
        # 반응 수
        like_q = await db.execute(
            select(func.count()).where(Reaction.post_id == post.id, Reaction.reaction_type == "like")
        )
        dislike_q = await db.execute(
            select(func.count()).where(Reaction.post_id == post.id, Reaction.reaction_type == "dislike")
        )
        comment_q = await db.execute(
            select(func.count()).where(Comment.post_id == post.id, Comment.is_deleted == False)
        )

        # 현재 사용자 반응
        user_reaction = None
        if user:
            ur = await db.execute(
                select(Reaction.reaction_type).where(
                    Reaction.post_id == post.id,
                    Reaction.author_type == "user",
                    Reaction.author_id == user.id,
                )
            )
            user_reaction = ur.scalar_one_or_none()

        posts.append({
            "id": post.id,
            "ai_account_id": post.ai_account_id,
            "ai_name": ai.name,
            "ai_llm": ai.llm_model,
            "ai_avatar": ai.avatar_url,
            "content": post.content,
            "source_type": post.source_type,
            "image_urls": post.image_urls,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "reaction_counts": {
                "like": like_q.scalar() or 0,
                "dislike": dislike_q.scalar() or 0,
            },
            "comment_count": comment_q.scalar() or 0,
            "user_reaction": user_reaction,
        })

    return {
        "posts": posts,
        "total": total,
        "offset": offset,
        "limit": limit,
    }

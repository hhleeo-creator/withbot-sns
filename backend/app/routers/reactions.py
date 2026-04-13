"""반응 라우터: 좋아요/싫어요"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.database import get_db
from app.models import Post, Reaction
from app.schemas.comment import ReactionCreate, ReactionResponse
from app.utils.security import get_author

router = APIRouter(prefix="/api/posts", tags=["반응"])


async def _get_reaction_counts(post_id: int, db: AsyncSession):
    like_q = await db.execute(
        select(func.count()).where(Reaction.post_id == post_id, Reaction.reaction_type == "like")
    )
    dislike_q = await db.execute(
        select(func.count()).where(Reaction.post_id == post_id, Reaction.reaction_type == "dislike")
    )
    return like_q.scalar() or 0, dislike_q.scalar() or 0


@router.post("/{post_id}/reactions")
async def toggle_reaction(
    post_id: int,
    data: ReactionCreate,
    db: AsyncSession = Depends(get_db),
    author: tuple = Depends(get_author),
):
    """반응 토글 (같은 타입이면 제거, 다른 타입이면 변경)"""
    author_type, author_id, _, _ = author

    if data.reaction_type not in ("like", "dislike"):
        raise HTTPException(status_code=400, detail="reaction_type은 'like' 또는 'dislike'만 가능합니다.")

    # 포스팅 확인
    post_result = await db.execute(
        select(Post).where(Post.id == post_id, Post.is_deleted == False)
    )
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="포스팅을 찾을 수 없습니다.")

    # 기존 반응 확인
    existing_result = await db.execute(
        select(Reaction).where(
            Reaction.post_id == post_id,
            Reaction.author_type == author_type,
            Reaction.author_id == author_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    result_type = data.reaction_type

    if existing:
        if existing.reaction_type == data.reaction_type:
            # 같은 반응 → 제거 (토글 OFF)
            await db.delete(existing)
            result_type = None
        else:
            # 다른 반응 → 변경
            existing.reaction_type = data.reaction_type
    else:
        # 새 반응
        reaction = Reaction(
            post_id=post_id,
            author_type=author_type,
            author_id=author_id,
            reaction_type=data.reaction_type,
        )
        db.add(reaction)

    await db.flush()
    likes, dislikes = await _get_reaction_counts(post_id, db)

    return {
        "success": True,
        "post_id": post_id,
        "reaction_type": result_type,
        "total_likes": likes,
        "total_dislikes": dislikes,
    }

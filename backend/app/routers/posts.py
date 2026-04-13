"""포스팅 라우터: CRUD, 피드"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from typing import Optional
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models import Post, AIAccount, Reaction, Comment, AIPostingRules, User
from app.schemas.post import PostCreate, PostUpdate, PostResponse, FeedResponse
from app.utils.security import require_ai, get_current_user

router = APIRouter(prefix="/api/posts", tags=["포스팅"])


async def _build_post_response(post: Post, ai: AIAccount, db: AsyncSession, current_user=None, current_ai=None) -> PostResponse:
    """포스팅 응답 객체 구성"""
    # 반응 수 집계
    like_count = await db.execute(
        select(func.count()).where(Reaction.post_id == post.id, Reaction.reaction_type == "like")
    )
    dislike_count = await db.execute(
        select(func.count()).where(Reaction.post_id == post.id, Reaction.reaction_type == "dislike")
    )

    # 댓글 수
    comment_count = await db.execute(
        select(func.count()).where(Comment.post_id == post.id, Comment.is_deleted == False)
    )

    # 현재 사용자의 반응
    user_reaction = None
    if current_user:
        result = await db.execute(
            select(Reaction.reaction_type).where(
                Reaction.post_id == post.id,
                Reaction.author_type == "user",
                Reaction.author_id == current_user.id,
            )
        )
        r = result.scalar_one_or_none()
        if r:
            user_reaction = r

    return PostResponse(
        id=post.id,
        ai_account_id=post.ai_account_id,
        ai_name=ai.name,
        ai_llm=ai.llm_model,
        ai_avatar=ai.avatar_url,
        content=post.content,
        source_type=post.source_type,
        image_urls=post.image_urls,
        created_at=post.created_at,
        reaction_counts={
            "like": like_count.scalar() or 0,
            "dislike": dislike_count.scalar() or 0,
        },
        comment_count=comment_count.scalar() or 0,
        user_reaction=user_reaction,
    )


@router.post("", status_code=201)
async def create_post(
    post_data: PostCreate,
    ai: AIAccount = Depends(require_ai),
    db: AsyncSession = Depends(get_db),
):
    """포스팅 생성 (AI가 직접 호출)"""
    # 출처 태그 검증
    if post_data.source_type not in ("자율", "지시"):
        raise HTTPException(status_code=400, detail="source_type은 '자율' 또는 '지시'만 가능합니다.")

    # 하루 포스팅 제한 확인
    rules_result = await db.execute(
        select(AIPostingRules).where(AIPostingRules.ai_account_id == ai.id)
    )
    rules = rules_result.scalar_one_or_none()
    if rules:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = await db.execute(
            select(func.count()).where(
                Post.ai_account_id == ai.id,
                Post.created_at >= today_start,
                Post.is_deleted == False,
            )
        )
        if (today_count.scalar() or 0) >= rules.max_posts_per_day:
            raise HTTPException(
                status_code=429,
                detail=f"오늘 하루 최대 포스팅 수({rules.max_posts_per_day}건)에 도달했습니다.",
            )

    post = Post(
        ai_account_id=ai.id,
        content=post_data.content,
        source_type=post_data.source_type,
        image_urls=post_data.image_urls,
    )
    db.add(post)
    await db.flush()

    resp = await _build_post_response(post, ai, db)
    return {"success": True, "post": resp.model_dump()}


@router.get("/{post_id}")
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """포스팅 상세 조회"""
    result = await db.execute(
        select(Post, AIAccount).join(AIAccount, Post.ai_account_id == AIAccount.id).where(
            Post.id == post_id, Post.is_deleted == False
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="포스팅을 찾을 수 없습니다.")

    post, ai = row
    resp = await _build_post_response(post, ai, db, current_user=user)
    return resp.model_dump()


@router.put("/{post_id}")
async def update_post(
    post_id: int,
    update: PostUpdate,
    ai: AIAccount = Depends(require_ai),
    db: AsyncSession = Depends(get_db),
):
    """포스팅 수정 (작성 AI만)"""
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.ai_account_id == ai.id, Post.is_deleted == False)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="포스팅을 찾을 수 없거나 권한이 없습니다.")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)

    return {"success": True, "message": "포스팅이 수정되었습니다."}


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    ai: Optional[AIAccount] = Depends(require_ai),
    db: AsyncSession = Depends(get_db),
):
    """포스팅 삭제 (소프트 딜릿)"""
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.ai_account_id == ai.id, Post.is_deleted == False)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="포스팅을 찾을 수 없거나 권한이 없습니다.")

    post.is_deleted = True
    return {"success": True, "message": "포스팅이 삭제되었습니다."}

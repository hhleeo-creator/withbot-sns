"""댓글 라우터: 댓글/대댓글 CRUD"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Post, Comment, Notification, AIAccount, User
from app.schemas.comment import CommentCreate, CommentUpdate
from app.utils.security import get_author

router = APIRouter(prefix="/api", tags=["댓글"])


@router.post("/posts/{post_id}/comments", status_code=201)
async def create_comment(
    post_id: int,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    author: tuple = Depends(get_author),
):
    """포스팅에 댓글/대댓글 작성 (인간 또는 AI)"""
    author_type, author_id, author_name, author_avatar = author

    # 포스팅 확인
    post_result = await db.execute(
        select(Post).where(Post.id == post_id, Post.is_deleted == False)
    )
    post = post_result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="포스팅을 찾을 수 없습니다.")

    # 대댓글인 경우 부모 댓글 확인
    if data.parent_comment_id:
        parent_result = await db.execute(
            select(Comment).where(
                Comment.id == data.parent_comment_id,
                Comment.post_id == post_id,
                Comment.is_deleted == False,
            )
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="부모 댓글을 찾을 수 없습니다.")

    comment = Comment(
        post_id=post_id,
        author_type=author_type,
        author_id=author_id,
        parent_comment_id=data.parent_comment_id,
        content=data.content,
    )
    db.add(comment)
    await db.flush()

    # 알림 생성: 포스팅 작성 AI의 주인에게
    ai_result = await db.execute(
        select(AIAccount).where(AIAccount.id == post.ai_account_id)
    )
    post_ai = ai_result.scalar_one_or_none()
    if post_ai and not (author_type == "ai" and author_id == post_ai.id):
        notification = Notification(
            ai_account_id=post_ai.id,
            owner_id=post_ai.owner_id,
            notification_type="comment_received",
            related_comment_id=comment.id,
            related_post_id=post_id,
            message=f"{author_name}님이 댓글을 달았습니다: {data.content[:50]}",
        )
        db.add(notification)

    return {
        "success": True,
        "comment": {
            "id": comment.id,
            "post_id": post_id,
            "author_type": author_type,
            "author_id": author_id,
            "author_name": author_name,
            "author_avatar": author_avatar,
            "content": comment.content,
            "parent_comment_id": comment.parent_comment_id,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
        },
    }


@router.get("/posts/{post_id}/comments")
async def get_comments(
    post_id: int,
    db: AsyncSession = Depends(get_db),
):
    """포스팅 댓글 목록 (트리 구조)"""
    result = await db.execute(
        select(Comment)
        .where(Comment.post_id == post_id, Comment.is_deleted == False)
        .order_by(Comment.created_at.asc())
    )
    all_comments = result.scalars().all()

    # 작성자 이름 조회를 위한 맵 구성
    async def get_author_info(comment):
        if comment.author_type == "ai":
            r = await db.execute(select(AIAccount).where(AIAccount.id == comment.author_id))
            ai = r.scalar_one_or_none()
            return (ai.name if ai else "알 수 없는 AI", ai.avatar_url if ai else None)
        else:
            r = await db.execute(select(User).where(User.id == comment.author_id))
            user = r.scalar_one_or_none()
            return (user.name if user else "알 수 없는 사용자", user.avatar_url if user else None)

    # 트리 구조 변환
    comment_map = {}
    roots = []

    for c in all_comments:
        name, avatar = await get_author_info(c)
        item = {
            "id": c.id,
            "post_id": c.post_id,
            "author_type": c.author_type,
            "author_id": c.author_id,
            "author_name": name,
            "author_avatar": avatar,
            "content": c.content,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "replies": [],
        }
        comment_map[c.id] = item

        if c.parent_comment_id and c.parent_comment_id in comment_map:
            comment_map[c.parent_comment_id]["replies"].append(item)
        else:
            roots.append(item)

    return {"comments": roots, "total": len(all_comments)}


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    author: tuple = Depends(get_author),
):
    """댓글 삭제 (작성자만)"""
    author_type, author_id, _, _ = author
    result = await db.execute(
        select(Comment).where(
            Comment.id == comment_id,
            Comment.author_type == author_type,
            Comment.author_id == author_id,
            Comment.is_deleted == False,
        )
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없거나 권한이 없습니다.")

    comment.is_deleted = True
    return {"success": True, "message": "댓글이 삭제되었습니다."}

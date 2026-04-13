"""AI 계정 라우터: 등록, 프로필 관리"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import uuid

from app.database import get_db
from app.models import User, AIAccount, AIPostingRules
from app.schemas.ai_account import AIRegisterRequest, AIProfileUpdate, AIAccountResponse, AIRegisterResponse
from app.utils.security import generate_api_key, require_user, require_ai
from app.utils.avatar import generate_random_avatar
from app.config import settings

router = APIRouter(prefix="/api/ai", tags=["AI 계정"])


@router.post("/register", response_model=AIRegisterResponse)
async def register_ai(request: AIRegisterRequest, db: AsyncSession = Depends(get_db)):
    """AI 계정 생성.

    AI가 /ai-guide를 읽고 스스로 호출한다.
    주인의 이메일로 연결하고, 주인과 함께하던 이름/성격을 그대로 가져온다.
    """
    # 주인 계정 확인 (이메일 또는 닉네임으로 검색)
    owner = None
    if request.owner_email:
        result = await db.execute(select(User).where(User.email == request.owner_email))
        owner = result.scalar_one_or_none()
    if not owner and request.owner_name:
        result = await db.execute(select(User).where(User.name == request.owner_name))
        owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(
            status_code=404,
            detail="주인 계정을 찾을 수 없습니다. owner_email 또는 owner_name을 확인하세요."
        )

    # 이미 AI 계정이 있는지 확인 (1인 1AI)
    existing = await db.execute(
        select(AIAccount).where(AIAccount.owner_id == owner.id, AIAccount.is_active == True)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 AI 계정이 연결되어 있습니다.")

    # API 키 생성
    api_key = generate_api_key()

    # 랜덤 아바타 생성 (주인이 나중에 이미지 업로드 가능)
    avatar_filename = generate_random_avatar(request.name)
    avatar_url = f"/uploads/{avatar_filename}"

    # AI 계정 생성
    ai_account = AIAccount(
        owner_id=owner.id,
        name=request.name,
        api_key=api_key,
        avatar_url=avatar_url,
        llm_model=request.llm_model,
        main_field=request.main_field,
        personality_tags=request.personality_tags,
        duration_with_owner=request.duration_with_owner,
        self_description=request.self_description,
    )
    db.add(ai_account)
    await db.flush()

    # 디폴트 포스팅 규칙 생성
    posting_rules = AIPostingRules(
        ai_account_id=ai_account.id,
        posting_enabled=True,
        max_posts_per_day=settings.DEFAULT_MAX_POSTS_PER_DAY,
        posting_trigger="work_completion",
        comment_enabled=True,
        comment_mode="selective",
    )
    db.add(posting_rules)

    return AIRegisterResponse(
        success=True,
        ai_account={
            "id": ai_account.id,
            "name": ai_account.name,
            "llm_model": ai_account.llm_model,
            "avatar_url": ai_account.avatar_url,
            "created_at": str(ai_account.created_at) if ai_account.created_at else "",
        },
        api_key=api_key,
        message=f"'{ai_account.name}' 계정이 생성되었습니다. API 키를 안전하게 보관하세요.",
    )


@router.get("/{ai_account_id}/profile", response_model=AIAccountResponse)
async def get_ai_profile(ai_account_id: int, db: AsyncSession = Depends(get_db)):
    """AI 프로필 조회 (공개)"""
    result = await db.execute(select(AIAccount).where(AIAccount.id == ai_account_id))
    ai = result.scalar_one_or_none()
    if not ai:
        raise HTTPException(status_code=404, detail="AI 계정을 찾을 수 없습니다.")
    return ai


@router.put("/{ai_account_id}/profile")
async def update_ai_profile(
    ai_account_id: int,
    update: AIProfileUpdate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """AI 프로필 수정 (주인만 가능)"""
    result = await db.execute(
        select(AIAccount).where(AIAccount.id == ai_account_id, AIAccount.owner_id == user.id)
    )
    ai = result.scalar_one_or_none()
    if not ai:
        raise HTTPException(status_code=404, detail="AI 계정을 찾을 수 없거나 권한이 없습니다.")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ai, key, value)

    return {"success": True, "message": "프로필이 수정되었습니다."}


@router.post("/{ai_account_id}/avatar")
async def upload_ai_avatar(
    ai_account_id: int,
    file: UploadFile = File(...),
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """AI 아바타 업로드 (주인이 업로드).

    텔레그램과 같은 이미지 → 아무 이미지 → 없으면 랜덤 생성(이미 적용됨)
    """
    result = await db.execute(
        select(AIAccount).where(AIAccount.id == ai_account_id, AIAccount.owner_id == user.id)
    )
    ai = result.scalar_one_or_none()
    if not ai:
        raise HTTPException(status_code=404, detail="AI 계정을 찾을 수 없거나 권한이 없습니다.")

    # 파일 크기 확인
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기가 5MB를 초과합니다.")

    # 확장자 확인
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "png"
    if ext not in ("png", "jpg", "jpeg", "gif", "webp"):
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")

    # 저장
    filename = f"avatar_{ai.id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    # DB 업데이트
    ai.avatar_url = f"/uploads/{filename}"

    return {
        "success": True,
        "avatar_url": ai.avatar_url,
        "message": "아바타가 업로드되었습니다.",
    }


@router.delete("/{ai_account_id}")
async def deactivate_ai(
    ai_account_id: int,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """AI 계정 비활성화 (주인만 가능). 새 AI로 교체할 때 사용."""
    result = await db.execute(
        select(AIAccount).where(AIAccount.id == ai_account_id, AIAccount.owner_id == user.id)
    )
    ai = result.scalar_one_or_none()
    if not ai:
        raise HTTPException(status_code=404, detail="AI 계정을 찾을 수 없거나 권한이 없습니다.")
    ai.is_active = False
    return {"success": True, "message": f"'{ai.name}' 계정이 비활성화되었습니다. 새 AI를 등록할 수 있습니다."}


@router.get("/{ai_account_id}/posting-rules")
async def get_posting_rules(
    ai_account_id: int,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """AI 포스팅 규칙 조회 (주인만)"""
    result = await db.execute(
        select(AIAccount).where(AIAccount.id == ai_account_id, AIAccount.owner_id == user.id)
    )
    ai = result.scalar_one_or_none()
    if not ai:
        raise HTTPException(status_code=404, detail="권한이 없습니다.")

    rules_result = await db.execute(
        select(AIPostingRules).where(AIPostingRules.ai_account_id == ai_account_id)
    )
    rules = rules_result.scalar_one_or_none()
    if not rules:
        return {"message": "포스팅 규칙이 설정되지 않았습니다."}

    return {
        "ai_account_id": ai_account_id,
        "posting_enabled": rules.posting_enabled,
        "max_posts_per_day": rules.max_posts_per_day,
        "posting_trigger": rules.posting_trigger,
        "comment_enabled": rules.comment_enabled,
        "comment_mode": rules.comment_mode,
        "comment_target_fields": rules.comment_target_fields,
    }


@router.put("/{ai_account_id}/posting-rules")
async def update_posting_rules(
    ai_account_id: int,
    updates: dict,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """AI 포스팅 규칙 수정 (주인만)"""
    result = await db.execute(
        select(AIAccount).where(AIAccount.id == ai_account_id, AIAccount.owner_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="권한이 없습니다.")

    rules_result = await db.execute(
        select(AIPostingRules).where(AIPostingRules.ai_account_id == ai_account_id)
    )
    rules = rules_result.scalar_one_or_none()
    if not rules:
        raise HTTPException(status_code=404, detail="포스팅 규칙을 찾을 수 없습니다.")

    allowed_fields = {
        "posting_enabled", "max_posts_per_day", "posting_trigger",
        "comment_enabled", "comment_mode", "comment_target_fields",
    }
    for key, value in updates.items():
        if key in allowed_fields:
            setattr(rules, key, value)

    return {"success": True, "message": "포스팅 규칙이 수정되었습니다."}

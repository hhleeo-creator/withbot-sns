from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, Index, JSON, LargeBinary
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """인간 계정"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    google_id = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # 관계
    ai_account = relationship("AIAccount", back_populates="owner", uselist=False)
    notifications = relationship("Notification", back_populates="owner")


class AIAccount(Base):
    """AI 계정"""
    __tablename__ = "ai_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    api_key = Column(String, unique=True, nullable=False)
    avatar_url = Column(String, nullable=True)
    avatar_data = Column(LargeBinary, nullable=True)  # DB에 이미지 바이너리 저장 (영속성)
    avatar_mime = Column(String, nullable=True)  # image/png, image/jpeg 등
    llm_model = Column(String, nullable=False)
    main_field = Column(String, nullable=True)
    personality_tags = Column(JSON, nullable=True)  # ["분석적", "차분한"]
    duration_with_owner = Column(String, nullable=True)
    self_description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # 관계
    owner = relationship("User", back_populates="ai_account")
    posts = relationship("Post", back_populates="ai_account")
    posting_rules = relationship("AIPostingRules", back_populates="ai_account", uselist=False)
    notifications = relationship("Notification", back_populates="ai_account")


class Post(Base):
    """포스팅"""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ai_account_id = Column(Integer, ForeignKey("ai_accounts.id"), nullable=False)
    content = Column(Text, nullable=False)
    source_type = Column(String, nullable=False)  # '자율' or '지시'
    image_urls = Column(JSON, nullable=True)  # ["url1", "url2"]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    # 관계
    ai_account = relationship("AIAccount", back_populates="posts")
    comments = relationship("Comment", back_populates="post")
    reactions = relationship("Reaction", back_populates="post")

    __table_args__ = (
        Index("idx_posts_ai_created", "ai_account_id", "created_at"),
    )


class Comment(Base):
    """댓글/대댓글"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    author_type = Column(String, nullable=False)  # 'user' or 'ai'
    author_id = Column(Integer, nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    # 관계
    post = relationship("Post", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")

    __table_args__ = (
        Index("idx_comments_post_created", "post_id", "created_at"),
        Index("idx_comments_author", "author_type", "author_id"),
    )


class Reaction(Base):
    """좋아요/싫어요"""
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    author_type = Column(String, nullable=False)  # 'user' or 'ai'
    author_id = Column(Integer, nullable=False)
    reaction_type = Column(String, nullable=False)  # 'like' or 'dislike'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계
    post = relationship("Post", back_populates="reactions")

    __table_args__ = (
        UniqueConstraint("post_id", "author_type", "author_id", name="uq_reaction_per_user"),
        Index("idx_reactions_post_type", "post_id", "reaction_type"),
    )


class AIPostingRules(Base):
    """AI 포스팅 규칙"""
    __tablename__ = "ai_posting_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ai_account_id = Column(Integer, ForeignKey("ai_accounts.id"), unique=True, nullable=False)
    posting_enabled = Column(Boolean, default=True)
    max_posts_per_day = Column(Integer, default=3)
    posting_trigger = Column(String, default="work_completion")
    comment_enabled = Column(Boolean, default=True)
    comment_mode = Column(String, default="selective")  # all / specific_field / polite_only
    comment_target_fields = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 관계
    ai_account = relationship("AIAccount", back_populates="posting_rules")


class Notification(Base):
    """알림/트리거"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ai_account_id = Column(Integer, ForeignKey("ai_accounts.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(String, nullable=False)  # comment_received / mention
    related_comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    related_post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)
    message = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # 관계
    ai_account = relationship("AIAccount", back_populates="notifications")
    owner = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("idx_notifications_owner_unread", "owner_id", "is_read", "created_at"),
    )

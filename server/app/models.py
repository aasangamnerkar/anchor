from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, JSON, UniqueConstraint, Index

# =========================================================
# DATABASE MODELS
# =========================================================

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Auth
    email: str = Field(unique=True, index=True)
    password_hash: str
    email_verified: bool = Field(default=False, nullable=False)

    # Basic profile
    name: Optional[str] = None
    school: Optional[str] = Field(default=None, max_length=150)

    # Location/profile context
    current_location: Optional[str] = Field(default=None, max_length=255)
    anchor_location: Optional[str] = Field(default=None, max_length=255)

    # Lifestyle / matching context
    budget: Optional[float] = Field(default=None)
    preferences: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False)
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )

    sent_friend_requests: List["FriendRequest"] = Relationship(
        back_populates="requester",
        sa_relationship_kwargs={"foreign_keys": "[FriendRequest.requester_id]"},
    )
    received_friend_requests: List["FriendRequest"] = Relationship(
        back_populates="receiver",
        sa_relationship_kwargs={"foreign_keys": "[FriendRequest.receiver_id]"},
    )

    friendships_as_low: List["Friendship"] = Relationship(
        back_populates="user_low",
        sa_relationship_kwargs={"foreign_keys": "[Friendship.user_low_id]"},
    )
    friendships_as_high: List["Friendship"] = Relationship(
        back_populates="user_high",
        sa_relationship_kwargs={"foreign_keys": "[Friendship.user_high_id]"},
    )


class FriendRequest(SQLModel, table=True):
    """
    One directional request: requester -> receiver.
    """
    __tablename__ = "friend_requests"

    id: Optional[int] = Field(default=None, primary_key=True)

    requester_id: int = Field(foreign_key="users.id", index=True)
    receiver_id: int = Field(foreign_key="users.id", index=True)

    status: str = Field(default="pending", max_length=20)
    # pending, accepted, declined, canceled

    message: Optional[str] = Field(default=None, max_length=280)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = None
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )

    requester: Optional["User"] = Relationship(
        back_populates="sent_friend_requests",
        sa_relationship_kwargs={"foreign_keys": "[FriendRequest.requester_id]"},
    )
    receiver: Optional["User"] = Relationship(
        back_populates="received_friend_requests",
        sa_relationship_kwargs={"foreign_keys": "[FriendRequest.receiver_id]"},
    )

    __table_args__ = (
        UniqueConstraint("requester_id", "receiver_id", name="uq_friend_request_pair"),
        Index("ix_friend_requests_receiver_status", "receiver_id", "status"),
    )


class Friendship(SQLModel, table=True):
    """
    Store accepted friendships as a single row with canonical ordering:
    (user_low_id, user_high_id)
    """
    __tablename__ = "friendships"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_low_id: int = Field(foreign_key="users.id", index=True)
    user_high_id: int = Field(foreign_key="users.id", index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    user_low: Optional["User"] = Relationship(
        back_populates="friendships_as_low",
        sa_relationship_kwargs={"foreign_keys": "[Friendship.user_low_id]"},
    )
    user_high: Optional["User"] = Relationship(
        back_populates="friendships_as_high",
        sa_relationship_kwargs={"foreign_keys": "[Friendship.user_high_id]"},
    )

    __table_args__ = (
        UniqueConstraint("user_low_id", "user_high_id", name="uq_friendship_pair"),
        Index("ix_friendships_user_low", "user_low_id"),
        Index("ix_friendships_user_high", "user_high_id"),
    )


from pydantic import BaseModel, EmailStr, Field as PydanticField
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    school: Optional[str] = None
    current_location: Optional[str] = None
    anchor_location: Optional[str] = None
    budget: Optional[float] = None
    preferences: List[str] = PydanticField(default_factory=list)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    school: Optional[str] = None
    current_location: Optional[str] = None
    anchor_location: Optional[str] = None
    budget: Optional[float] = None
    preferences: Optional[List[str]] = None


class UserRead(BaseModel):
    id: int
    email: EmailStr
    email_verified: bool = False
    name: Optional[str] = None
    school: Optional[str] = None
    current_location: Optional[str] = None
    anchor_location: Optional[str] = None
    budget: Optional[float] = None
    preferences: List[str] = PydanticField(default_factory=list)
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
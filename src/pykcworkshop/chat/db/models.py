"""The SQLAlchemy ORM schema."""

from __future__ import annotations

import datetime
from typing import Any, Optional

from dotenv import load_dotenv
from sqlalchemy import Column, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from pykcworkshop import utils
from pykcworkshop.chat import constants
from pykcworkshop.chat.db.columns import UTCDateTime

load_dotenv()


class BaseModel(AsyncAttrs, DeclarativeBase):
    """Base ORM class for all db tables."""

    created_date: Mapped[datetime.date] = mapped_column(default=datetime.date.today)

    def __repr__(self) -> str:  # pragma: no cover
        columns = ", ".join([f"{col}={val}" for col, val in self.as_dict().items()])
        return f"{self.__class__.__name__}({columns})"

    def as_dict(self) -> dict[str, Any]:  # pragma: no cover
        """Convert this model to a dict of its column names and values."""

        new_dict = {col.key: getattr(self, col.key) for col in self.__table__.columns}
        return new_dict


table_room_member = Table(
    "room_member",
    BaseModel.metadata,
    Column(
        "room_id",
        ForeignKey("room.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    ),
    Column(
        "member_id",
        ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    ),
)
"""Intermediate table for the many;many room_member relationship between rooms and users."""


class HashedToken(BaseModel):
    """An ORM model representing a hashed JWT."""

    __tablename__ = "hashed_token"

    id: Mapped[str] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(unique=True)
    is_revoked: Mapped[bool] = mapped_column(default=False)


class Room(BaseModel):
    """An ORM model representing a Chatroom."""

    __tablename__ = "room"

    id: Mapped[str] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(constants.NAME_LENGTH, collation="NOCASE"))
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    owner: Mapped["User"] = relationship(foreign_keys=[owner_id], lazy="selectin")
    members: Mapped[list["User"]] = relationship(
        secondary=table_room_member,
        back_populates="joined_rooms",
        lazy="selectin",
    )

    __table_args__ = (UniqueConstraint(name, owner_id),)


class User(BaseModel):
    """An ORM model representing a Chat User."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(constants.NAME_LENGTH, collation="NOCASE"), unique=True
    )
    hashed_token_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("hashed_token.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    hashed_token: Mapped[Optional["HashedToken"]] = relationship(
        foreign_keys=[hashed_token_id], lazy="selectin"
    )
    joined_rooms: Mapped[list["Room"]] = relationship(
        secondary=table_room_member,
        back_populates="members",
        lazy="selectin",
    )


class ChatMessage(BaseModel):
    """An ORM model representing a single chat message."""

    __tablename__ = "chat_message"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    author: Mapped["User"] = relationship(foreign_keys=[author_id], lazy="selectin")
    room_id: Mapped[str] = mapped_column(
        ForeignKey("room.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    room: Mapped["Room"] = relationship(foreign_keys=[room_id], lazy="selectin")
    content: Mapped[str] = mapped_column(String(512))
    timestamp: Mapped[UTCDateTime] = mapped_column(UTCDateTime, default=utils.now)

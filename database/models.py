from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, ForeignKey, Integer, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram User ID
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    participations: Mapped[list["Participant"]] = relationship(back_populates="user")

class Contest(Base):
    __tablename__ = "contests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    media_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    winner_count: Mapped[int] = mapped_column(Integer, default=1)
    max_participants: Mapped[int | None] = mapped_column(Integer, nullable=True) # Maksimal ishtirokchi chegarasi
    button_text: Mapped[str] = mapped_column(String(255), default="🎁 Konkursda Qatnashish")
    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) # Boshlanish vaqti
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False) # Tugash vaqti


    creator_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sponsors: Mapped[list["SponsorChannel"]] = relationship(back_populates="contest", cascade="all, delete-orphan")
    participants: Mapped[list["Participant"]] = relationship(back_populates="contest", cascade="all, delete-orphan")

class SponsorChannel(Base):
    __tablename__ = "sponsor_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contest_id: Mapped[int] = mapped_column(Integer, ForeignKey("contests.id", ondelete="CASCADE"))
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Telegram Channel ID (e.g. -100...)
    channel_title: Mapped[str] = mapped_column(String(255), nullable=False)
    invite_link: Mapped[str] = mapped_column(String(500), nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)

    contest: Mapped["Contest"] = relationship(back_populates="sponsors")

class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contest_id: Mapped[int] = mapped_column(Integer, ForeignKey("contests.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ticket_code: Mapped[str] = mapped_column(String(50), nullable=False)

    contest: Mapped["Contest"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(back_populates="participations")

import uuid
import enum
from zoneinfo import ZoneInfo
from datetime import datetime

from sqlalchemy import Column, Table, ForeignKey, String, CheckConstraint, Enum, ForeignKeyConstraint, DDL, event
import sqlalchemy.types as types
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func

from typing import Optional

from common import models

UserIdType = String(256)

class TimezoneSQLType(types.TypeDecorator):
    impl = types.VARCHAR
    cache_ok = True

    def process_bind_param(self, value: ZoneInfo, dialect) -> str:
        return value.key
    
    def process_result_value(self, value: str, dialect) -> ZoneInfo:
        return ZoneInfo(value)


class Base(DeclarativeBase):
    type_annotation_map = {
        ZoneInfo: TimezoneSQLType
    }

tags_to_events = Table(
    "tags_to_events",
    Base.metadata,
    Column("event_id", ForeignKey("events.id", ondelete="cascade", onupdate="cascade"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="cascade", onupdate="cascade"), primary_key=True),
)

user_settings_selected_categories = Table(
    "user_settings_selected_categories",
    Base.metadata,
    Column("user_id", UserIdType, primary_key=True),
    Column("acc_type", Enum(models.AccountType), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
    ForeignKeyConstraint(
        ["user_id", "acc_type"],
        ["event_settings.user_id", "event_settings.user_acc_type"],
        ondelete="cascade",
        onupdate="cascade"
    ),
)

class TagsTable(Base):
    __tablename__ = "tags"

    id: Mapped[int]  = mapped_column(primary_key=True, unique=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)

class EventsTable(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("end_date_utc IS NOT NULL", name="date_check"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    user_acc_type: Mapped[models.AccountType] = mapped_column(nullable=False, primary_key=True)
    user_id: Mapped[str] = mapped_column(UserIdType)
    parsed_at: Mapped[datetime] = mapped_column(nullable=False, default=func.CURRENT_TIMESTAMP())

    event_name: Mapped[str] = mapped_column(String(128))
    start_date_utc: Mapped[Optional[datetime]] # Always stores UTC ISO-8601 datetime
    end_date_utc: Mapped[datetime] # Always stores UTC ISO-8601 datetime
    address: Mapped[str] = mapped_column(String(256))
    email_link: Mapped[str] = mapped_column(String(256))

    tags: Mapped[list[TagsTable]] = relationship(secondary=tags_to_events, lazy="joined")

class CalendarLinksTable(Base):
    __tablename__ = "calendar_links"

    user_id: Mapped[str] = mapped_column(UserIdType, primary_key=True, unique=True)
    user_acc_type: Mapped[models.AccountType] = mapped_column(nullable=False, primary_key=True)
    calendar_identifier: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4)

class EventSettingsTable(Base):
    __tablename__ = "event_settings"

    user_id: Mapped[str] = mapped_column(UserIdType, primary_key=True, unique=True)
    user_acc_type: Mapped[models.AccountType] = mapped_column(nullable=False, primary_key=True)
    
    categories: Mapped[list[TagsTable]] = relationship(secondary=user_settings_selected_categories, lazy="joined")

# A scheduled event that automatically deletes events older than 6 months
remove_old_events = DDL(
    "CREATE EVENT IF NOT EXISTS remove_old_events"
    "   ON SCHEDULE EVERY 4 HOUR"
    "   DO"
    "       DELETE FROM events WHERE parsed_at < CURRENT_TIMESTAMP() - INTERVAL 6 MONTH"
)
event.listen(Base.metadata, "after_create", remove_old_events)
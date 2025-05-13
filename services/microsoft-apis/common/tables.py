import uuid
from zoneinfo import ZoneInfo
from datetime import datetime, tzinfo

from sqlalchemy import DateTime, ForeignKey, String, event, DDL
import sqlalchemy.types as types
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import DeclarativeBase, relationship

from typing import Optional

class Base(DeclarativeBase):
    pass

def tz_aware(dt: datetime) -> tzinfo | None:
    if(dt is not None and 
       dt.tzinfo is not None and 
       dt.tzinfo.utcoffset(dt) is not None):
        return dt.tzinfo
    else:
        return None

class _TimezoneSQLType(types.TypeDecorator):
    impl = types.VARCHAR
    cache_ok = True

    def process_bind_param(self, value: ZoneInfo, dialect) -> str:
        return value.key
    
    def process_result_value(self, value: str, dialect) -> ZoneInfo:
        return ZoneInfo(value)

class _UTCDateTimeSQLType(types.TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime, dialect) -> datetime:
        if(value is not None):
            value = value.astimezone(ZoneInfo("UTC"))
        return value
    
    def process_result_value(self, value: datetime, dialect) -> datetime:
        if(value is not None):
            value = value.replace(tzinfo=ZoneInfo("UTC"))
        return value
    
class UserInfoTable(Base):
    __tablename__ = "user_info"

    user_id: Mapped[str] = mapped_column(String(256), primary_key=True, unique=True)
    
    user_email: Mapped[str] = mapped_column(String(256))
    access_token: Mapped[str] = mapped_column(String(4096), nullable=True)
    access_token_expires: Mapped[datetime] = mapped_column(_UTCDateTimeSQLType(), nullable=True)
    refresh_token: Mapped[str] = mapped_column(String(2048), nullable=True)

class ParsedEmails(Base):
    __tablename__ = "parsed_emails"
    user_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    email_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    expire_at: Mapped[datetime] = mapped_column(_UTCDateTimeSQLType())

class TimezoneTable(Base):
    __tablename__ = "timezones"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timezone: Mapped[ZoneInfo] = mapped_column(_TimezoneSQLType(64), nullable=False, unique=True)

    _related_settings: Mapped[list["SettingsTable"]] = relationship(back_populates="timezone", lazy="joined")

class EmailSubscriptionsTable(Base):
    __tablename__ = "email_subscriptions"

    user_id: Mapped[str] = mapped_column(String(256), primary_key=True, unique=True)
    subscription_id: Mapped[str] = mapped_column(String(256))
    expires_at: Mapped[datetime] = mapped_column(_UTCDateTimeSQLType())

class SettingsTable(Base):
    __tablename__ = "settings"

    user_id: Mapped[str] = mapped_column(String(256), primary_key=True, unique=True)

    timezone_id: Mapped[int] = mapped_column(ForeignKey("timezones.id"))
    timezone: Mapped[TimezoneTable] = relationship(back_populates="_related_settings", lazy="joined")
    auto_fetch_emails: Mapped[bool] = mapped_column(default=False)

# An event that clears out expired email IDs from the parsed email cache
remove_expired_emails = DDL(
    "CREATE EVENT IF NOT EXISTS remove_expired_emails"
    "   ON SCHEDULE EVERY 6 HOUR"
    "   DO"
    "       DELETE FROM parsed_emails WHERE expire_at < UTC_TIMESTAMP()"
)
event.listen(Base.metadata, "after_create", remove_expired_emails)

# An event that removes expired subscriptions from the database
remove_old_subscriptions = DDL(
    "CREATE EVENT IF NOT EXISTS remove_old_subscriptions"
    "   ON SCHEDULE EVERY 4 HOUR"
    "   DO"
    "       DELETE FROM email_subscriptions WHERE expires_at < UTC_TIMESTAMP() - INTERVAL 2 HOUR"
)
event.listen(Base.metadata, "after_create", remove_old_subscriptions)

# A scheduled event that automatically disables auto_fetch_emails, 
# if for some reason subscription update was unsuccessful
keep_settings_consistent = DDL(
    "CREATE EVENT IF NOT EXISTS keep_settings_consistent"
    "   ON SCHEDULE EVERY 2 HOUR"
    "   DO"
    "       BEGIN"
    "           DECLARE finished INTEGER DEFAULT 0;"
    '           DECLARE user_id VARCHAR(256) DEFAULT "";'
    '           DECLARE subscription_id VARCHAR(256) DEFAULT NULL;'
    "           DECLARE settings_cursor CURSOR"
    "               FOR SELECT settings.user_id, email_subscriptions.subscription_id FROM settings LEFT JOIN email_subscriptions ON email_subscriptions.user_id = settings.user_id;"
    "           DECLARE CONTINUE HANDLER FOR NOT FOUND SET finished = 1;"
    "           OPEN settings_cursor;"
    "           fetch_rows: LOOP"
    "               FETCH settings_cursor INTO user_id, subscription_id;"
    "               IF finished = 1 THEN"
    "                   LEAVE fetch_rows;"
    "               END IF;"
    "               SET @uid = user_id;"
    "               IF subscription_id IS NULL THEN"
    "                   UPDATE settings SET auto_fetch_emails = 0 WHERE settings.user_id = @uid;"
    "               ELSE"
    "                    UPDATE settings SET auto_fetch_emails = 1 WHERE settings.user_id = @uid;"
    "               END IF;"
    "           END LOOP fetch_rows;"
    "           CLOSE settings_cursor;"
    "       END"
)
event.listen(Base.metadata, "after_create", keep_settings_consistent)
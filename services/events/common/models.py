import pydantic
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, field_validator, model_validator
import enum

from typing import Literal, Optional
from typing_extensions import Self

from datetime import datetime, tzinfo, timezone

# Based on https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive , checks if datetime object knows what timezone it is in
def tz_aware(dt: datetime) -> tzinfo | None:
    if(dt is not None and 
       dt.tzinfo is not None and 
       dt.tzinfo.utcoffset(dt) is not None):
        return dt.tzinfo
    else:
        return None

class AccountType(enum.Enum):
    OUTLOOK = "outlook"

class Tag(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

class EventBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_name: str = Field(description="Title given by the LLM for the event")
    start_date: Optional[datetime] = Field(description="Timestamp for event start date. If no timezone is specified, the timestamp will be treated as UTC.", validation_alias=AliasChoices("start_date", "start_date_utc"))
    end_date: datetime = Field(description="Timestamp for event end date. If no timezone is specified, the timestamp will be treated as UTC.", validation_alias=AliasChoices("end_date", "end_date_utc"))
    address: str
    email_link: str

    @pydantic.model_validator(mode="after")
    def validate_multiple_fields(self) -> Self:
        if(self.end_date == None):
            raise ValueError("'end_date' cannot be none")
        
        if(self.start_date != None and not tz_aware(self.start_date)):
            self.start_date = self.start_date.replace(tzinfo=timezone.utc)

        if(not tz_aware(self.end_date)):
            self.end_date = self.end_date.replace(tzinfo=timezone.utc)

        return self

class EventsGetRequest(BaseModel):
    direction: Literal["forward", "backward"] = Field(description="Tells the API endpoint whether to fetch events before or after a given date")
    from_time: datetime = Field(description="An ISO-8601 date-time string specifying the date to fetch events from (or up to). If no timezone is provided, then the time will be treated as an UTC timestamp.")

class EventsGetResponse(EventBase):
    id: int = Field(description="Event identifier in database")
    tags: list[Tag] = Field(description="Category tags for the event. Only tags from the /events/tags endpoint are listed.")

class EventsUpdateRequest(EventBase):
    tags: list[Tag] = Field(description="Category tags for the event. Only tags from the /events/tags endpoint are going to be included. Tags that aren't defined there will be ignored.")

class CalendarLinkResponse(BaseModel):
    link: str = Field(description="Calendar link's full URL")

class Settings(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    categories: list[Tag]

class ParsedEvent(BaseModel):
    event_name: str
    start_date: datetime | None
    end_date: datetime
    country: str
    city: str
    address: str
    room: str
    tags: list[str]
from fastapi import Depends, APIRouter, Request, Response, HTTPException

import uuid, hashlib

import icalendar, icalendar.prop
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import timezone, timedelta

import sys
sys.path.append('..')
from common import tables, models

import auth
from auth import UserData
import helpers
import db

def create_event_hash(event_row: tables.EventsTable) -> bytes:
    hash = hashlib.sha256(
        event_row.email_link.encode("utf-8") +
        event_row.parsed_at.isoformat().encode("utf-8")
    )

    return hash.hexdigest()


calendar_router = APIRouter(
    prefix="/api/events"
)

@calendar_router.get("/calendar/link/", include_in_schema=False) # avoid stupid redirects
@calendar_router.get("/calendar/link")
async def get_link(
    request: Request,
    user: UserData = Depends(auth.authenticate_user),
    db_session: AsyncSession = Depends(db.start_session),
) -> models.CalendarLinkResponse:
    """
    Authenticated API endpoint for fetching the calendar link
    """

    query = select(tables.CalendarLinksTable) \
            .where(
                tables.CalendarLinksTable.user_id == user.account_id, 
                tables.CalendarLinksTable.user_acc_type == user.account_type
            )
    query_result = await db_session.execute(query)

    link_row = query_result.scalar_one_or_none()
    if(link_row == None):
        raise HTTPException(status_code=404, detail="No calendar link found")
    
    return models.CalendarLinkResponse(
        link=helpers.format_calendar_link(link_row.calendar_identifier, request)
    )

@calendar_router.post("/calendar/link/", include_in_schema=False) # avoid stupid redirects
@calendar_router.post("/calendar/link")
async def generate_link(
    request: Request,
    user: UserData = Depends(auth.authenticate_user),
    db_session: AsyncSession = Depends(db.start_session),
) -> models.CalendarLinkResponse:
    """
    Authenticated API endpoint for creating or regenerating a calendar link
    """

    calendar_identifier = uuid.uuid4()

    query = select(tables.CalendarLinksTable) \
            .where(
                tables.CalendarLinksTable.user_id == user.account_id, 
                tables.CalendarLinksTable.user_acc_type == user.account_type
            )
    query_result = await db_session.execute(query)

    link_row = query_result.scalar_one_or_none()
    if(link_row != None):
        link_row.calendar_identifier = calendar_identifier
    else:
        row = tables.CalendarLinksTable(
            user_id=user.account_id,
            user_acc_type=user.account_type,
            calendar_identifier=calendar_identifier
        )
        db_session.add(row)

    await db_session.commit()

    return models.CalendarLinkResponse(
        link=helpers.format_calendar_link(calendar_identifier, request)
    )

@calendar_router.delete("/calendar/link/", status_code=204, include_in_schema=False) # avoid stupid redirects
@calendar_router.delete("/calendar/link", status_code=204)
async def delete_calendar_link(
    user: UserData = Depends(auth.authenticate_user),
    db_session: AsyncSession = Depends(db.start_session),
):
    """
    Authenticated API endpoint for deleting a calendar link for the user
    """

    query = delete(tables.CalendarLinksTable) \
            .where(
                tables.CalendarLinksTable.user_id == user.account_id, 
                tables.CalendarLinksTable.user_acc_type == user.account_type, 
            )
    query_result = await db_session.execute(query)
    await db_session.commit()

    if(query_result.rowcount == 0): # rowcount will be -1 for SQL db which will not support showing deleted rows
        raise HTTPException(status_code=404, detail="Calendar link not found")

    return

@calendar_router.get("/calendar/{calendar_id}/", include_in_schema=False) # avoid stupid redirects
@calendar_router.get("/calendar/{calendar_id}")
async def get_calendar_file(
    calendar_id: uuid.UUID,
    db_session: AsyncSession = Depends(db.start_session),
):
    """
    Unauthenticated API endpoint for converting found events to iCal format
    """
    
    calendar_query = select(tables.CalendarLinksTable) \
                    .where(tables.CalendarLinksTable.calendar_identifier == calendar_id)
    query_result = await db_session.execute(calendar_query)
    calendar_user = query_result.scalar_one_or_none()
    if(calendar_user == None):
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    query = select(tables.EventsTable) \
            .where(tables.EventsTable.user_id == calendar_user.user_id, tables.EventsTable.user_acc_type == calendar_user.user_acc_type) #\
    query_result = await db_session.stream(query)

    calendar = icalendar.Calendar()
    calendar["VERSION"] = "2.0"
    calendar["PRODID"] = "Events Organiser v1.0"

    async for (event_row, ) in query_result.unique():
        calendar_event = icalendar.Event()
        calendar_event["UID"] = uuid.UUID(create_event_hash(event_row)[:32])
        calendar_event["DTSTAMP"] = icalendar.vDatetime(event_row.parsed_at.astimezone(timezone.utc))

        calendar_event["SUMMARY"] = event_row.event_name
        if(event_row.start_date_utc is not None):
            calendar_event["DTSTART"] = icalendar.vDatetime(event_row.start_date_utc.replace(tzinfo=timezone.utc))
        else: # deadline
            calendar_event["DTSTART"] = icalendar.vDatetime(event_row.end_date_utc.replace(tzinfo=timezone.utc) - timedelta(minutes=15))

        calendar_event["DTEND"] = icalendar.vDatetime(event_row.end_date_utc.replace(tzinfo=timezone.utc))
        calendar_event["LOCATION"] = event_row.address # TODO: handle empty string cases
        calendar_event["CATEGORIES"] = icalendar.prop.vCategory([tag_row.name for tag_row in event_row.tags])
        calendar.add_component(calendar_event)

    return Response(calendar.to_ical(), media_type="text/calendar")
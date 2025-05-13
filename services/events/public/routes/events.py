from fastapi import Depends, APIRouter, Request, Response, HTTPException
from fastapi_pagination import Page, add_pagination, paginate
from fastapi.responses import JSONResponse
from fastapi_pagination.ext.sqlalchemy import paginate

import os, uuid

import icalendar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from datetime import timezone

import sys
sys.path.append('..')
from common import tables, models

import auth
from auth import UserData
import helpers
import db

events_router = APIRouter(
    prefix="/api/events"
)

@events_router.get("/all/", include_in_schema=False) # avoid stupid redirects
@events_router.get("/all")
async def get_events(
    request_data: models.EventsGetRequest = Depends(), # Required for the input parameters, so that FastAPI displays descriptions for query fields in Swagger
    user: UserData = Depends(auth.authenticate_user),
    db_session: AsyncSession = Depends(db.start_session)
) -> Page[models.EventsGetResponse]:
    """
    Authenticated API endpoint for listing events before or after a given date.
    The results are paginated in lists up to 100 events.
    """

    if(not models.tz_aware(request_data.from_time)):
        request_data.from_time = request_data.from_time.replace(tzinfo=timezone.utc)
    request_data.from_time = request_data.from_time.astimezone(timezone.utc) # NOTE: MySQL DATETIME comparision is done disregarding timezones, please always convert a non UTC datetime to an UTC one (since DATETIMEs in the database are stored as UTC)
 
    query = select(tables.EventsTable) \
            .where(
                tables.EventsTable.user_id == user.account_id, 
                tables.EventsTable.user_acc_type == user.account_type
            )
    if(request_data.direction == "forward"):
        query = query.where(tables.EventsTable.end_date_utc >= request_data.from_time)
    else:
        query = query.where(tables.EventsTable.end_date_utc < request_data.from_time)
        
    return await paginate(
        db_session,
        query
    )

@events_router.patch("/event/{id}/", status_code=204, include_in_schema=False) # avoid stupid redirects
@events_router.patch("/event/{id}", status_code=204)
async def update_event(
    id: int,
    new_data: models.EventsUpdateRequest,
    user: UserData = Depends(auth.authenticate_user),
    db_session: AsyncSession = Depends(db.start_session)
):
    """
    Authenticated API endpoint for updating event data
    """

    query = select(tables.EventsTable) \
            .where(
                tables.EventsTable.id == id,
                tables.EventsTable.user_id == user.account_id,
                tables.EventsTable.user_acc_type == user.account_type
            )
    
    query_result = await db_session.execute(query)
    event: tables.EventsTable = query_result.unique().scalar_one_or_none()
    if(event == None):
        raise HTTPException(status_code=404, detail=f"Event with id {id} not found")

    # new tags to replace old ones with
    new_tags_ids = [tag.id for tag in new_data.tags]

    tags_query = select(tables.TagsTable) \
                .filter(tables.TagsTable.id.in_(new_tags_ids))
    tags_query_result = await db_session.execute(tags_query)

    event.event_name = new_data.event_name
    event.start_date_utc = new_data.start_date
    event.end_date_utc = new_data.end_date
    event.address = new_data.address
    event.tags = []
    for (tag, ) in tags_query_result.all():
        event.tags.append(tag)

    await db_session.commit()

    return

@events_router.delete("/event/{id}/", status_code=204, include_in_schema=False) # avoid stupid redirects
@events_router.delete("/event/{id}", status_code=204)
async def delete_event(
    id: int,
    user: UserData = Depends(auth.authenticate_user),
    db_session: AsyncSession = Depends(db.start_session)
):
    """
    Authenticated API endpoint for deleting an event
    """

    query = delete(tables.EventsTable) \
            .where(
                tables.EventsTable.id == id,
                tables.EventsTable.user_id == user.account_id,
                tables.EventsTable.user_acc_type == user.account_type
            )
    
    query_result = await db_session.execute(query)
    await db_session.commit()

    if(query_result.rowcount == 0): # rowcount will be -1 for SQL db which will not support showing deleted rows
        raise HTTPException(status_code=404, detail=f"Event with id {id} not found")

    return

@events_router.get("/tags/", include_in_schema=False) # avoid stupid redirects
@events_router.get("/tags")
async def get_tags(
    db_session: AsyncSession = Depends(db.start_session)
) -> list[models.Tag]:
    """
    Unauthenticated API endpoint for fetching all available tags used for categorising events
    """
    query = select(tables.TagsTable)
    results = await db_session.execute(query)
    return results.scalars().all()
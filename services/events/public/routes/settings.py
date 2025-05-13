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

settings_router = APIRouter(
    prefix="/api/events"
)

@settings_router.get("/settings/", include_in_schema=False) # avoid stupid redirects
@settings_router.get("/settings")
async def get_settings(
    user: UserData = Depends(auth.authenticate_user),
    db_session: AsyncSession = Depends(db.start_session)
) -> models.Settings:
    """
    Authenticated API endpoint to fetch event related settings for user
    """
    query = select(tables.EventSettingsTable) \
            .where(
                tables.EventSettingsTable.user_id == user.account_id,
                tables.EventSettingsTable.user_acc_type == user.account_type
            )
    
    query_result = await db_session.execute(query)

    settings_row = query_result.unique().scalar_one_or_none()
    if(settings_row == None):
        raise HTTPException(status_code=404, detail="Settings have not been created for some reason")
    
    return models.Settings.model_validate(settings_row)

@settings_router.patch("/settings/", status_code=204, include_in_schema=False) # avoid stupid redirects
@settings_router.patch("/settings", status_code=204)
async def update_settings(
    new_settings: models.Settings,
    user: UserData = Depends(auth.authenticate_user),
    db_session: AsyncSession = Depends(db.start_session)
):
    """
    Authenticated API endpoint to update settings
    """
    query = select(tables.EventSettingsTable) \
            .where(
                tables.EventSettingsTable.user_id == user.account_id,
                tables.EventSettingsTable.user_acc_type == user.account_type
            )
    
    query_result = await db_session.execute(query)
    settings_row = query_result.unique().scalar_one()

    new_categories_ids = [cat.id for cat in new_settings.categories]
    categories_query = select(tables.TagsTable) \
            .filter(tables.TagsTable.id.in_(new_categories_ids))
    categories_query = await db_session.execute(categories_query)
    
    settings_row.categories = []
    for (category_tag, ) in categories_query.all():
        settings_row.categories.append(category_tag)

    await db_session.commit()
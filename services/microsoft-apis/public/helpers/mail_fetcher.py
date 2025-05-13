import asyncio
import itertools
from typing import Callable
from datetime import datetime

from helpers import graph_api

async def get_unparsed_emails_after_date(access_token: str, 
                                         parsed_emails: set[str],
                                         after_date: datetime,
                                         _filter: str | None) -> list[str]:
    """
    Gets a list of all unparsed emails for a user sent after a specified date

    :param access_token: Access token for the user account
    :param parsed_emails: Set of parsed email IDs
    :param after_date: Emails after this date will be fetched
    :param _filter: Filter for Microsoft Graph API

    :return: List of email IDs that have not yet been parsed
    """
    emails = await graph_api.read_emails_after_date(
        access_token,
        after_date=after_date,
        select=["id"],
        _filter=_filter
    )

    unparsed_email_ids = []
    for email in emails:
        if(email["id"] not in parsed_emails):
            unparsed_email_ids.append(email["id"])

    return unparsed_email_ids

async def fetch_emails_batched(
        ids_and_tokens: list[tuple[str, str]], 
        batch_size: int = 10,
        filter_func: Callable[[dict], bool] = lambda _: True) -> list[dict]:
    """
    Sends batched requests to Microsoft Graph API /me/messages endpoint to fetch emails.

    :param ids_and_tokens: List of tuples consisting of email ID and access token
    :param batch_size: Amount of asynchronous requests to send at a time
    :param filter_func: A callable that decides whether the email should be added to the list or not. 
        This function should return False if email should be ignored

    :raises RuntimeWarning: When the function is unable to fully fetch all emails

    :return: A list of emails that were fetched, in the same JSON format as Microsoft Graph returned
    """
    results = []
    for batch in itertools.batched(ids_and_tokens, batch_size):
        tasks: list[asyncio.Task] = []
        for item in batch:
            async with asyncio.TaskGroup() as tg:
                tasks.append(tg.create_task(graph_api.get_message(item[0], item[1])))

        for item, task in zip(batch, tasks):
            data = task.result()
            if(data["resp"].status != 200):
                raise RuntimeWarning("Failed to fetch all emails requested in a batch")

            if(filter_func(data["json_data"]) == False):
                continue

            results.append(data["json_data"])

    return results
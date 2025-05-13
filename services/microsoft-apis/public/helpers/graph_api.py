import aiohttp
from datetime import datetime, timezone, timedelta

class TokenUpdateError(Exception):
    pass

import certifi, ssl
sslcontext = ssl.create_default_context(cafile=certifi.where())

async def update_token_if_needed(
        access_token: str, 
        expires_at: datetime,
        refresh_token: str, 
        client_id: str,
        client_secret: str,
        scopes: list[str],
        tenant: str = "common",
        if_expires_in_less_than: timedelta = timedelta(minutes=5)) -> tuple[str, datetime, str] | None:
    """
    Exchanges a refresh token for a new Microsoft access token & refresh token, if the current one is about to expire

    :raises TokenUpdateError: If the response does not indicate that the refresh token has expired, but the response was erroneous (status code != 200)

    :return: None if the refresh token has expired and access token cannot be updated.
        Otherwise a tuple of: the token, the expiration date and the refresh token
    """

    if("offline_access" not in scopes):
        scopes.append("offline_access")

    if(expires_at - datetime.now(timezone.utc) < if_expires_in_less_than):
        async with aiohttp.ClientSession("https://login.microsoftonline.com") as session:
            async with session.post(
                f"/{tenant}/oauth2/v2.0/token",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "client_id": client_id,
                    "scope": " ".join(scopes),
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_secret": client_secret
                }, ssl=sslcontext) as resp:
                    resp_text = await resp.text()

                    if(resp.status == 200):
                        resp_data = await resp.json()
                        return (resp_data["access_token"], datetime.now(timezone.utc) + timedelta(seconds=resp_data["expires_in"]), resp_data["refresh_token"])
                    elif(resp.status == 400):
                        # check for an error that says that the refresh token has expired
                        resp_data = await resp.json()

                        if(any(error_code in resp_data["error_codes"] for error_code in [50173, 70000, 70043, 700082, 70008])):
                            return None

                        raise TokenUpdateError(f"Received 'Bad request' error trying to update token. Response: {resp_text}")
                    else:
                        raise TokenUpdateError(f"Received status code {resp.status} trying to update the token. Response: {resp_text}")
    else:
        return (access_token, expires_at, refresh_token)

async def get_messages(access_token: str, select: list | None, _filter: list | None, skip: int = 0, top: int = 100) -> dict:
    """
    Gets emails of a user from Microsoft Graph API
    
    :return: a dictionary containing
        "resp" - the response object,
        "json_data" - response body as json
    """
    params = {
        "$top": top,
        "$skip": skip
    }
    if(select):
        params["$select"] = ",".join(select)

    if(_filter):
        params["$filter"] = _filter

    async with aiohttp.ClientSession("https://graph.microsoft.com") as session:
        async with session.get(
                "/v1.0/me/messages", 
                params=params,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Prefer": 'outlook.body-content-type="text", IdType="ImmutableId"',
                }, ssl=sslcontext) as resp:
            resp_json = await resp.json()

            return {
                "resp": resp,
                "json_data": resp_json
            }

async def get_message(id: str, access_token: str, select: list | None = None) -> dict:
    """
    Gets the contents of a single email for a user from Microsoft Graph API

    :returns: a dictionary containing
        "resp" - the response object,
        "json_data" - response body as json
    """
    params = {}
    if(select):
        params["$select"] = ",".join(select)

    async with aiohttp.ClientSession("https://graph.microsoft.com/") as session:
        async with session.get(
                f"/v1.0/me/messages/{id}", 
                params=params,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Prefer": 'outlook.body-content-type="text", IdType="ImmutableId"',
                }, ssl=sslcontext) as resp:
            resp_json = await resp.json()

            return {
                "resp": resp,
                "json_data": resp_json
            }

async def create_subscription(access_token: str, notification_url: str, lifecycle_url: str, secret: str,
                              resource: str, expires_in: timedelta = timedelta(minutes=10000)) -> tuple[str, datetime] | None:
    """
    Creates a subscription for a user

    :param access_token: Access token for the user
    :param notification_url: URL to receive notifications to
    :param lifecycle_url: URL to receive updates about subscriptions (like reauth, expiration and missed notis)
    :param secret: A secret value that gets sent in a subscription. Use to verify the authenticity of a notification
    :param resource: MS Graph resource to subscribe to
    :param expires_in: Expiration date for the subscription. Default value is fetched from Microsoft Graph API docs

    :return: Subscription ID and the expiration date if the request was successful, otherwise None

            If a duplicate subscription already exists, then the ID of an already existing subscription is returned
    """

    expiration_date = datetime.now(timezone.utc) + expires_in
    async with aiohttp.ClientSession("https://graph.microsoft.com") as session:
        async with session.post(
            f"/v1.0/subscriptions",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Prefer": 'IdType="ImmutableId"',
            },
            json={
                "changeType": "created",
                "notificationUrl": notification_url,
                "lifecycleNotificationUrl": lifecycle_url,
                "resource": resource,
                "expirationDateTime": expiration_date.isoformat(),
                "clientState": secret
            }, ssl=sslcontext
        ) as resp:
            if(resp.status == 201):
                json_data = await resp.json()
                return (json_data["id"], datetime.fromisoformat(json_data["expirationDateTime"]))
            elif(resp.status == 409): # sub already exists
                # cant even test it because microsoft docs say one thing (dupe sub not allowed)
                # but in reality they actually do allow this
                raise NotImplementedError("This condition was never met during development")
            else:
                return None

async def delete_subscription(subscription_id: str, access_token: str) -> bool:
    """
    Deletes a Microsoft Graph subscription

    :param subscription_id: Subscription ID
    :param access_token: Access token for the user

    :return: True if the deletion was successful, or if there was no subscription to delete.
        Returns False if an error occurred
    """
    async with aiohttp.ClientSession("https://graph.microsoft.com") as session:
        async with session.delete(
            f"/v1.0/subscriptions/{subscription_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            ssl=sslcontext
        ) as resp:
            if(resp.status == 404 or 200 <= resp.status <= 299):
                return True
            
    return False

async def extend_subscription(subscription_id: str, access_token: str, extend_by: timedelta = timedelta(minutes=10000)) -> tuple[bool, datetime] | None:
    """
    Extends a Microsoft Graph subscription by a predetermined amount. This also has the effect of reauthorizing the subscription.

    :param subscription_id: Subscription ID
    :param access_token: Access token for the user
    :param extend_by: The amount of time to extend the subscription by. Depends on the resource.

    :return: None if the subscription could not be extended.
        On success, returns a tuple of boolean that says whether the subscription exists & a new expiration date. 
        Expiration date will be None if the subscription does not exist
    """
    async with aiohttp.ClientSession("https://graph.microsoft.com") as session:
        async with session.patch(
            f"/v1.0/subscriptions/{subscription_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Prefer": 'IdType="ImmutableId"'
            },
            json={
                "expirationDateTime": datetime.now(timezone.utc) + extend_by
            },
            ssl=sslcontext
        ) as resp:
            if(resp.status == 404):
                return False, None
            elif(200 <= resp.status <= 299):
                resp_data = await resp.json()
                return True, datetime.fromisoformat(resp_data["expirationDateTime"])
            
    return None

async def read_emails_after_date(
        access_token: str, 
        select: list | None,
        _filter: str | None,
        after_date: datetime, 
        skip: int = 0, 
        top: int = 100) -> dict:
    """
    Fetches emails for a Microsoft user after a specified UTC time
    
    :param access_token: Access token for the user account
    :param select: Resource properties to be fetched by Microsoft Graph
    :param after_date: Time point that is used to cut off email fetching (older emails will not be fetched)
    :param skip: Number of emails to skip
    :param top: Amount of emails to fetch in a single batch internally

    :return: Emails that the user received after "after_date"
    """
    emails = []
    if("sentDateTime" not in select):
        select.append("sentDateTime")

    while True:
        result = await get_messages(access_token, select=select, _filter=_filter, skip=skip, top=top)
        if(len(result["json_data"]["value"]) == 0): # no more emails to read from user
            break
        
        added_emails = 0
        for email in result["json_data"]["value"]:
            if(datetime.fromisoformat(email["sentDateTime"]) <= after_date):
                continue

            emails.append(email)

        if(added_emails == 0): # none found after date
            break

        skip += top

    return emails
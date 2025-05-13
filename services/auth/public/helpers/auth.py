import aiohttp
import jwt, jwt.exceptions
from fastapi import Response, HTTPException, Cookie
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
from asyncache import cached
from cachetools import TTLCache

from pydantic import BaseModel, Field

import certifi, ssl, os
sslcontext = ssl.create_default_context(cafile=certifi.where())

import server_config

DEFAULT_EXPIRATION_TIME = timedelta(minutes=30)

@cached(TTLCache(2, 600))
async def get_ms_signing_keys() -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get('https://login.microsoftonline.com/common/discovery/v2.0/keys', ssl=sslcontext) as response:
            resp_json = await response.json()
            return resp_json

def find_key(token: str, keys: list[dict]) -> str | None:
    header = jwt.get_unverified_header(token)
    decrypt_key = None
    for key in keys["keys"]:
        if(key["kid"] == header["kid"]):
            decrypt_key = key
            break

    return decrypt_key

class UserData(BaseModel):
    email: str = Field(alias="sub")
    account_type: str
    account_id: str

async def authenticate_user(
    response: Response,
    cookie_value: str = Cookie(
        alias=server_config.JWT_SESSION_COOKIE_NAME,
        title="JWT storage cookie",
        description="A cookie that includes the encoded JWT token for any account type"
    )
) -> UserData:
    """
    Authenticates a user based on the session cookie contained JWT token.

    Raises:
        HTTPException when JWT fails validation.

    Returns:
        Returns the JWT data if it is valid.
    """
    if(cookie_value == None):
        raise HTTPException(status_code=401, detail="This endpoint requires authentication")
    
    try:
        decoded_data = jwt.decode(
            jwt=cookie_value,
            key=server_config.JWT_SECRET,
            algorithms=["HS256"],
            leeway=timedelta(seconds=10)
        )

        return UserData.model_validate(decoded_data)
    except jwt.exceptions.ExpiredSignatureError:
        response.delete_cookie(server_config.JWT_SESSION_COOKIE_NAME)
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

async def decode_jwt_token(id_token: str, audience: str) -> tuple[dict | None, str]:
    """Verifies that a JWT is signed by a valid (trusted) public key. Decodes the token

       Returns the decoded token if it is valid, otherwise None and an error message
    """
    keys = await get_ms_signing_keys()
    decrypt_key = find_key(id_token, keys)

    if(decrypt_key == None):
        return None, f"Key not found in Microsoft Entra tenant-independent key endpoint"
    
    try:
        decoded = jwt.decode(
            jwt=id_token,
            key=jwt.PyJWK.from_dict(decrypt_key),
            algorithms=["RS256"],
            audience=audience
        )
    except jwt.exceptions.ExpiredSignatureError as e:
        return None, f"JWT token is expired ({e})"
    except jwt.exceptions.InvalidTokenError as e:
        return None, f"Unable to decode token due to some issue ({e})"
    return decoded, ""

def create_jwt_from_microsoft(id_token_data: dict, secret: str, expiration: timedelta = DEFAULT_EXPIRATION_TIME) -> str:
    """Creates a JWT token from Microsoft's id_token data"""
    data = {}
    data["account_id"] = id_token_data["oid"]
    data["account_type"] = "outlook"
    # metadata
    data["sub"] = id_token_data["email"]

    # TODO: maybe check that the given expiration time does not surpass id_token's
    data["exp"] = datetime.now(timezone.utc) + expiration

    return jwt.encode(
        data, 
        secret
    )

def set_jwt_cookie(name: str, value: str, response: Response, expiration: timedelta = DEFAULT_EXPIRATION_TIME):
    """Puts a Set-Cookie header in the HTTP response to carry the JWT"""
    response.set_cookie(
        key=name,
        value=value,
        secure=True,
        expires=datetime.now(timezone.utc)+expiration
    )
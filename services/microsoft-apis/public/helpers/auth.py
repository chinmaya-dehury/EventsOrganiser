from fastapi import Response, HTTPException, Cookie
from datetime import timedelta
from pydantic import BaseModel, Field
import jwt, jwt.exceptions

import server_config

class UserData(BaseModel):
    email: str = Field(alias="sub")
    account_type: str
    account_id: str

async def authenticate_user(
    response: Response,
    cookie_value: str = Cookie(
        alias=server_config.JWT_SESSION_COOKIE_NAME,
        title="JWT storage cookie",
        description="A cookie that includes the encoded JWT token, provided by Auth endpoint"
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

        user = UserData.model_validate(decoded_data)
        if(user.account_type != "outlook"):
            raise HTTPException(status_code=403, detail="Account is not a Microsoft account")

        return user
    except jwt.exceptions.ExpiredSignatureError:
        response.delete_cookie(server_config.JWT_SESSION_COOKIE_NAME)
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
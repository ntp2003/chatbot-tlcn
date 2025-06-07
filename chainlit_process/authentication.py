import datetime
import chainlit as cl
from repositories.user import (
    password_auth_user,
    UserRole,
    get_by_email_and_role,
    create as create_user,
    CreateUserModel,
    update as update_user,
    UpdateUserModel,
)
from service.google_api import get_gender
from typing import Dict, Optional
from models.user import OAuthProvider


# decorator chainlit regis hàm auth_callback gọi khi user xác thực bằng mật khẩu
@cl.password_auth_callback  # type: ignore
def password_auth_callback(username: str, password: str) -> Optional[cl.User]:
    user = password_auth_user(username, password, UserRole.chainlit_user)

    if not user:
        return None

    return cl.User(identifier=str(user.id), metadata={"user_id": str(user.id)})


@cl.oauth_callback
async def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
    id_token: Optional[str] = None,
) -> Optional[cl.User]:
    if provider_id == "google":
        email = raw_user_data.get("email")
        verified_email = raw_user_data.get("verified_email", False)
        if isinstance(verified_email, str):
            verified_email = verified_email.lower() == "true"

        google_id = raw_user_data.get("id")

        if not email or not verified_email or not google_id:
            return None

        if google_user := get_by_email_and_role(email, UserRole.google_user):
            google_user.last_oauth_login = datetime.datetime.now()

            update_data = UpdateUserModel(**google_user.model_dump())
            update_user(google_user.id, update_data)
            return cl.User(
                identifier=str(google_user.id),
                metadata={"user_id": str(google_user.id), "provider": "google"},
            )

        full_name = raw_user_data.get("name")
        gender = get_gender(token, google_id)

        create_data = CreateUserModel(
            user_name=email,
            password=None,  # Password is not used for OAuth users
            email=email,
            email_verified=verified_email or False,
            full_name=full_name,
            google_id=google_id,
            role=UserRole.google_user,
            oauth_provider=OAuthProvider.google,
            gender=gender,
            last_oauth_login=datetime.datetime.now(),
        )
        new_user = create_user(create_data)
        return cl.User(
            identifier=str(new_user.id),
            metadata={"user_id": str(new_user.id), "provider": "google"},
        )
    return None

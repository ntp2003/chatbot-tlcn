from typing import Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def get_gender(access_token: str, profile_id: str) -> Optional[str]:
    try:
        creds = Credentials(token=access_token)
        service = build("people", "v1", credentials=creds)
        profile = (
            service.people()
            .get(resourceName=f"people/{profile_id}", personFields="genders")
            .execute()
        )
        return profile["genders"][0]["value"]
    except Exception as e:
        print(f"An error occurred while: {e}")
        return

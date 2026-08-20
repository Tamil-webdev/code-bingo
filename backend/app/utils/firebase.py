"""Firebase ID token verification via Google Identity Toolkit REST API."""

import httpx
from fastapi import HTTPException, status
from app.config import settings


async def verify_firebase_id_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return the account info."""
    url = (
        f"https://identitytoolkit.googleapis.com/v1/accounts:lookup"
        f"?key={settings.FIREBASE_API_KEY}"
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json={"idToken": id_token})

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token",
        )

    data = response.json()
    users = data.get("users", [])
    if not users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase account not found",
        )

    account = users[0]
    return {
        "uid": account.get("localId"),
        "email": account.get("email"),
        "display_name": account.get("displayName"),
        "email_verified": account.get("emailVerified", False),
    }

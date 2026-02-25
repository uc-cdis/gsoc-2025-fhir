from fastapi import HTTPException, status
import httpx
from .config import settings

async def verify_token(token: str) -> bool:

    if not token:
        return False
    return True


async def get_accessible_resources(token: str) -> list[str]:
 
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=settings.PROXY_TIMEOUT) as client:
        try:
            response = await client.get(
                f"{settings.AUTH_SERVER_URL}/auth/resources",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Failed to verify access permissions"
            ) from exc

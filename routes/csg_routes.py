from fastapi import APIRouter, HTTPException
from utils import format_application, get_token

csg_routes = APIRouter()


@csg_routes.get("/get-token")
async def get_token_endpoint():
    try:
        token = get_token()
        return {"success": True, "token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

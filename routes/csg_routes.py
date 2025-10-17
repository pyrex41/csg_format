from fastapi import APIRouter, HTTPException, Depends
from utils import format_application, get_token
from auth import get_current_user

csg_routes = APIRouter()


@csg_routes.get("/get-token")
async def get_token_endpoint(current_user: dict = Depends(get_current_user)):
    try:
        token = get_token()
        return {"success": True, "token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

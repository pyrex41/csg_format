from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth import authenticate_user, create_session, get_current_user

auth_router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: str
    expires_at: str
    message: str

@auth_router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return a session token.

    The token should be included in subsequent requests as:
    Authorization: Bearer {token}
    """
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    session = create_session(request.username)

    return LoginResponse(
        success=True,
        token=session["token"],
        expires_at=session["expires_at"],
        message="Login successful"
    )

@auth_router.get("/verify")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """
    Verify that the current token is valid.
    """
    return {
        "success": True,
        "username": current_user["username"],
        "message": "Token is valid"
    }

@auth_router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout the current user (invalidate token).
    """
    # In a real implementation, you would remove the token from the sessions store
    return {
        "success": True,
        "message": "Logged out successfully"
    }

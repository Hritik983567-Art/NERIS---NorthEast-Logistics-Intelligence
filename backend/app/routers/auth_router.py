from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Header, status
from pydantic import BaseModel
from app.adapters.aws_cognito import get_cognito_adapter
from app.core.dependencies import get_current_user

router = APIRouter(tags=["Amazon Cognito Auth & RBAC"])

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    name: Optional[str] = None
    role: Optional[str] = "FIELD_OFFICER"
    organization: Optional[str] = "NER Logistics Center"

class LoginRequest(BaseModel):
    username: str
    password: str
    role: Optional[str] = None

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
@router.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
@router.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
async def cognito_register(req: RegisterRequest):
    """
    Amazon Cognito User Registration Endpoint:
    Registers a new user in Cognito and server-side profile store with locked RBAC role assignment.
    """
    if not req.username or not req.email or not req.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation Error: 'username', 'email', and 'password' are required for registration."
        )

    # Security: Lock self-registered user accounts to FIELD_OFFICER role to prevent privilege escalation / role manipulation
    assigned_role = "FIELD_OFFICER"
    if req.role and req.role.upper() == "FIELD_OFFICER":
        assigned_role = "FIELD_OFFICER"

    adapter = get_cognito_adapter()
    result = adapter.register_user(
        username=req.username,
        email=req.email,
        password=req.password,
        name=req.name,
        role=assigned_role,
        organization=req.organization
    )

    return {
        "status": "REGISTERED",
        "message": result.get("message"),
        "user": result.get("user_profile"),
        "cognito_confirmed": result.get("cognito_confirmed", False)
    }

@router.post("/auth/login", status_code=status.HTTP_200_OK)
@router.post("/api/auth/login", status_code=status.HTTP_200_OK)
@router.post("/api/v1/auth/login", status_code=status.HTTP_200_OK)
async def cognito_login(req: LoginRequest):
    """
    Amazon Cognito Login Endpoint:
    Validates user credentials against Amazon Cognito User Pool.
    Role is strictly determined by server identity profile, NOT client browser payload!
    Returns Access Token, Refresh Token, ID Token, and User RBAC Profile.
    """
    if not req.username or not req.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation Error: 'username' and 'password' are required."
        )

    adapter = get_cognito_adapter()
    result = adapter.authenticate_user(
        username=req.username,
        password=req.password
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed: Invalid username or password."
        )

    return {
        "status": "AUTHENTICATED",
        "access_token": result.get("access_token"),
        "refresh_token": result.get("refresh_token"),
        "id_token": result.get("id_token"),
        "user": result.get("user"),
        "auth_provider": result.get("auth_provider")
    }

@router.post("/auth/logout", status_code=status.HTTP_200_OK)
@router.post("/api/auth/logout", status_code=status.HTTP_200_OK)
@router.post("/api/v1/auth/logout", status_code=status.HTTP_200_OK)
async def cognito_logout(authorization: Optional[str] = Header(None)):
    """
    Amazon Cognito Logout Endpoint:
    Revokes the current Bearer token session.
    """
    if not authorization:
        raise HTTPException(status_code=400, detail="Missing Authorization header.")

    adapter = get_cognito_adapter()
    result = adapter.logout_token(authorization)
    return result

@router.post("/auth/refresh", status_code=status.HTTP_200_OK)
@router.post("/api/auth/refresh", status_code=status.HTTP_200_OK)
@router.post("/api/v1/auth/refresh", status_code=status.HTTP_200_OK)
async def cognito_refresh(req: RefreshRequest):
    """
    Amazon Cognito Token Refresh Endpoint:
    Consumes a refresh token and generates a new access token.
    """
    adapter = get_cognito_adapter()
    result = adapter.refresh_access_token(req.refresh_token)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Refresh failed."))
    return result

@router.get("/auth/me", status_code=status.HTTP_200_OK)
@router.get("/api/auth/me", status_code=status.HTTP_200_OK)
@router.get("/api/v1/auth/me", status_code=status.HTTP_200_OK)
async def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieves current authenticated session details verified via Cognito token server-side.
    """
    return {
        "authenticated": True,
        "user": current_user.get("profile", current_user)
    }

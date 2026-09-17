import logging
from typing import List, Dict, Any, Callable
from fastapi import Header, HTTPException, status, Depends
from app.adapters.aws_cognito import get_cognito_adapter

logger = logging.getLogger("neris.security")

async def get_current_user(authorization: str = Header(None)) -> Dict[str, Any]:
    """
    FastAPI Security Dependency: Validates incoming Bearer token using Amazon Cognito or Dev Fallback.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Required: Missing 'Authorization' header in request.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    adapter = get_cognito_adapter()
    result = adapter.verify_token(authorization)

    if not result.get("is_valid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Authorization Token: {result.get('error', 'Token verification failed.')}",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return result

def require_roles(allowed_roles: List[str]):
    """
    FastAPI Security Role Enforcement Dependency Factory.
    Enforces Role-Based Access Control (RBAC) on protected API endpoints.
    Supported roles: COMMANDER, FIELD_OFFICER, DISPATCHER, ADMIN.
    """
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role", "FIELD_OFFICER").upper()
        allowed_upper = [r.upper() for r in allowed_roles]

        # ADMIN role always bypasses restricted endpoints
        if "ADMIN" in user_role or user_role in allowed_upper:
            return current_user

        logger.warning(
            f"Unauthorized access attempt by user '{current_user.get('username')}' "
            f"with role '{user_role}'. Required roles: {allowed_upper}"
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Denied: Role '{user_role}' is not authorized to access this operational resource. Required roles: {allowed_upper}"
        )

    return role_checker

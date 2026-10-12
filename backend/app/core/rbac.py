"""Role-Based Access Control (RBAC) & Identity Middleware — Network Control Plane"""

from enum import Enum
from typing import List, Optional
from fastapi import Header, HTTPException, status, Depends
from pydantic import BaseModel


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class CurrentUser(BaseModel):
    user_id: str
    role: UserRole


def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_id: Optional[str] = Header("system-admin", alias="X-User-Id"),
    x_user_role: Optional[str] = Header("admin", alias="X-User-Role"),
) -> CurrentUser:
    """Extract and validate current user identity and assigned role from Bearer JWT or request headers."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        from app.core.auth.jwt import decode_access_token
        payload = decode_access_token(token)
        if payload:
            uid = payload.get("user_id") or payload.get("sub") or "jwt-user"
            r_str = payload.get("role", "admin").lower()
            try:
                return CurrentUser(user_id=uid, role=UserRole(r_str))
            except ValueError:
                pass

    role_str = (x_user_role or "admin").lower()
    try:
        role = UserRole(role_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user role '{x_user_role}'. Valid roles are: {[r.value for r in UserRole]}",
        )

    return CurrentUser(user_id=x_user_id or "anonymous", role=role)


def require_role(allowed_roles: List[UserRole]):
    """FastAPI dependency factory enforcing RBAC role permissions."""
    async def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. User role '{current_user.role.value}' is not authorized for this operation. Required: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return dependency

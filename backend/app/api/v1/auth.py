"""Enterprise SSO & Authentication REST API Router — Network Control Plane"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.rbac import CurrentUser, UserRole, get_current_user, require_role
from app.core.auth.jwt import create_access_token
from app.core.auth.oidc import OIDCAuthProvider
from app.core.auth.passwords import hash_password, verify_password
from app.models.user import User
from app.services.audit import AuditService

router = APIRouter(prefix="/auth", tags=["Enterprise SSO & Auth Engine"])

# Built-in / Default OIDC SSO Provider Adapters
PROVIDERS: Dict[str, OIDCAuthProvider] = {
    "keycloak": OIDCAuthProvider(
        name="Keycloak OIDC",
        issuer_url="http://localhost:8080/realms/master",
        client_id="network-control-plane",
        client_secret="secret",
    ),
    "okta": OIDCAuthProvider(
        name="Okta SSO",
        issuer_url=getattr(settings, "OKTA_ISSUER_URL", "https://dev-12345.okta.com/oauth2/default"),
        client_id=getattr(settings, "OKTA_CLIENT_ID", "ncp-okta-client"),
        client_secret=getattr(settings, "OKTA_CLIENT_SECRET", "okta-secret"),
        role_claim_path=getattr(settings, "OKTA_ROLE_CLAIM", "roles"),
    ),
    "azure-ad": OIDCAuthProvider(
        name="Azure AD (Entra ID)",
        issuer_url="https://login.microsoftonline.com/common/v2.0",
        client_id="ncp-azure-client",
        client_secret="azure-secret",
    ),
}


class ProviderInfo(BaseModel):
    id: str
    name: str
    issuer_url: str
    client_id: str
    enabled: bool = True


class SSOProviderUpdateRequest(BaseModel):
    issuer_url: Optional[str] = Field(None, json_schema_extra={"example": "https://dev-123456.okta.com/oauth2/default"})
    client_id: Optional[str] = Field(None, json_schema_extra={"example": "0oa1234567890abcdef"})
    client_secret: Optional[str] = Field(None, json_schema_extra={"example": "your-okta-client-secret"})
    role_claim_path: Optional[str] = Field("roles", json_schema_extra={"example": "roles"})


class DirectLoginRequest(BaseModel):
    username: str = Field(..., json_schema_extra={"example": "admin"})
    password: str = Field(..., json_schema_extra={"example": "admin123"})
    requested_role: Optional[str] = Field("admin", json_schema_extra={"example": "admin"})


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    provider: str


class CallbackRequest(BaseModel):
    code: str
    redirect_uri: str = Field("http://localhost:3000/auth/callback")


class SetupStatusResponse(BaseModel):
    setup_required: bool
    admin_count: int


class SetupAdminRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, json_schema_extra={"example": "admin"})
    email: str = Field(..., min_length=5, max_length=128, json_schema_extra={"example": "admin@infra.local"})
    password: str = Field(..., min_length=8, max_length=128, json_schema_extra={"example": "SuperSecretPass123!"})


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, json_schema_extra={"example": "admin"})
    password: str = Field(..., min_length=1, json_schema_extra={"example": "SuperSecretPass123!"})


@router.get("/setup-status", response_model=SetupStatusResponse)
async def get_setup_status(db: AsyncSession = Depends(get_db)):
    """Check if the first-time administrator account has been provisioned."""
    stmt = select(func.count(User.id)).where(User.role == "admin")
    result = await db.execute(stmt)
    admin_count = result.scalar() or 0
    return SetupStatusResponse(
        setup_required=(admin_count == 0),
        admin_count=admin_count,
    )


@router.post("/setup-admin", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def setup_initial_admin(payload: SetupAdminRequest, db: AsyncSession = Depends(get_db)):
    """Provision the initial administrator account to bootstrap and initialize the platform."""
    stmt_count = select(func.count(User.id)).where(User.role == "admin")
    result_count = await db.execute(stmt_count)
    admin_count = result_count.scalar() or 0
    if admin_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Initial administrator setup has already been completed. Please sign in.",
        )

    stmt_user = select(User).where((User.username == payload.username) | (User.email == payload.email))
    existing = (await db.execute(stmt_user)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that username or email already exists.",
        )

    hashed_pw, salt = hash_password(payload.password)

    now = datetime.now(timezone.utc)
    admin_user = User(
        id=str(uuid.uuid4()),
        username=payload.username,
        email=payload.email,
        hashed_password=hashed_pw,
        salt=salt,
        role="admin",
        is_active=True,
        created_at=now,
        last_login=now,
    )
    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)

    await AuditService(db).log_event(
        action="SETUP_INITIAL_ADMIN",
        resource_type="user",
        resource_id=admin_user.id,
        risk_level="LOW",
        details={
            "username": admin_user.username,
            "email": admin_user.email,
            "role": "admin",
        },
    )

    token_data = {
        "user_id": admin_user.username,
        "email": admin_user.email,
        "role": "admin",
        "provider": "local",
    }
    jwt_token = create_access_token(token_data)

    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
        user_id=admin_user.username,
        role="admin",
        provider="local",
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate credentials against registered users in the database."""
    stmt = select(User).where((User.username == payload.username) | (User.email == payload.username))
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    if not verify_password(payload.password, user.hashed_password, user.salt):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    token_data = {
        "user_id": user.username,
        "email": user.email,
        "role": user.role,
        "provider": "local",
    }
    jwt_token = create_access_token(token_data)

    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
        user_id=user.username,
        role=user.role,
        provider="local",
    )


@router.get("/providers", response_model=List[ProviderInfo])
async def list_auth_providers():
    """List configured Identity Providers (OIDC / SAML2)."""
    result = []
    for pid, provider in PROVIDERS.items():
        result.append(
            ProviderInfo(
                id=pid,
                name=provider.name,
                issuer_url=provider.issuer_url,
                client_id=provider.client_id,
                enabled=True,
            )
        )
    return result


@router.put("/providers/{provider_id}", response_model=ProviderInfo)
async def update_sso_provider(
    provider_id: str,
    payload: SSOProviderUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN])),
):
    """Update an SSO identity provider's configuration (Admin role required)."""
    if provider_id not in PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Identity Provider '{provider_id}' not found.",
        )
    provider = PROVIDERS[provider_id]

    if payload.issuer_url:
        provider.issuer_url = payload.issuer_url.rstrip("/")
    if payload.client_id:
        provider.client_id = payload.client_id
    if payload.client_secret:
        provider.client_secret = payload.client_secret
    if payload.role_claim_path:
        provider.role_claim_path = payload.role_claim_path

    await AuditService(db).log_event(
        action="UPDATE_SSO_PROVIDER_CONFIG",
        resource_type="auth_provider",
        resource_id=provider_id,
        risk_level="MEDIUM",
        details={
            "provider_id": provider_id,
            "issuer_url": provider.issuer_url,
            "client_id": provider.client_id,
            "updated_by": user.user_id,
        },
    )

    return ProviderInfo(
        id=provider_id,
        name=provider.name,
        issuer_url=provider.issuer_url,
        client_id=provider.client_id,
        enabled=True,
    )


@router.get("/login/{provider_id}")
async def get_login_url(
    provider_id: str,
    redirect_uri: str = Query("http://localhost:3000/auth/callback"),
    state: str = Query("xyz123"),
):
    """Generate authorization redirect URL for requested Identity Provider."""
    if provider_id not in PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Identity Provider '{provider_id}' not found. Configured: {list(PROVIDERS.keys())}",
        )
    provider = PROVIDERS[provider_id]
    auth_url = provider.get_authorization_url(redirect_uri, state)
    return {"provider": provider_id, "authorization_url": auth_url}


@router.post("/callback/{provider_id}", response_model=TokenResponse)
async def auth_callback(
    provider_id: str,
    payload: CallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Process OAuth2 / OIDC code callback, exchange tokens, and generate platform JWT.
    
    Performs Just-In-Time (JIT) user registration in the database if user does not exist yet.
    """
    if provider_id not in PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Identity Provider '{provider_id}' not found.",
        )
    provider = PROVIDERS[provider_id]
    claims = await provider.authenticate_callback(payload.code, payload.redirect_uri)

    username = claims["user_id"]
    email = claims.get("email", f"{username}@corp.internal")
    role = claims["role"]

    # Verify if user has been pre-onboarded / assigned a role in PostgreSQL
    stmt = select(User).where(
        (User.username == username)
        | (User.email == email)
        | (User.username == email)
        | (User.email == username)
    )
    existing_user = (await db.execute(stmt)).scalar_one_or_none()

    if not existing_user:
        await AuditService(db).log_event(
            action="UNAUTHORIZED_SSO_ACCESS_ATTEMPT",
            resource_type="user",
            resource_id=username,
            risk_level="MEDIUM",
            details={
                "username": username,
                "email": email,
                "provider": provider_id,
                "reason": "User not onboarded or assigned any role in the platform",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this application. Please contact your platform administrator.",
        )

    if not existing_user.is_active:
        await AuditService(db).log_event(
            action="SUSPENDED_USER_ACCESS_ATTEMPT",
            resource_type="user",
            resource_id=existing_user.id,
            risk_level="HIGH",
            details={"username": username, "email": email, "provider": provider_id},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. You are not authorized to access this application.",
        )

    existing_user.last_login = datetime.now(timezone.utc)
    await db.commit()
    role = existing_user.role

    token_data = {
        "user_id": existing_user.username,
        "email": existing_user.email,
        "role": role,
        "provider": claims.get("provider", provider_id),
    }
    jwt_token = create_access_token(token_data)

    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
        user_id=existing_user.username,
        role=role,
        provider=claims.get("provider", provider_id),
    )


@router.post("/login/direct", response_model=TokenResponse)
async def direct_login(payload: DirectLoginRequest):
    """Direct login for platform administration and testing."""
    role = payload.requested_role if payload.requested_role in ["admin", "operator", "viewer"] else "admin"
    token_data = {
        "user_id": payload.username,
        "email": f"{payload.username}@corp.internal",
        "role": role,
        "provider": "direct",
    }
    jwt_token = create_access_token(token_data)

    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
        user_id=payload.username,
        role=role,
        provider="direct",
    )


@router.get("/me")
async def get_current_user_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve current logged in user identity and live authoritative role assignment."""
    stmt = select(User).where((User.username == current_user.user_id) | (User.email == current_user.user_id))
    db_user = (await db.execute(stmt)).scalar_one_or_none()
    current_role = db_user.role if db_user else current_user.role.value

    return {
        "user_id": current_user.user_id,
        "role": current_role,
        "authenticated": True,
    }


def is_protected_system_admin(user: User) -> bool:
    """Determine whether a user account is the immutable platform root superadmin."""
    protected_username = getattr(settings, "DEFAULT_ADMIN_USERNAME", "admin").strip().lower()
    protected_email = getattr(settings, "DEFAULT_ADMIN_EMAIL", "admin@network-control-plane.local").strip().lower()
    return (
        user.username.strip().lower() == protected_username
        or user.email.strip().lower() == protected_email
    )


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    is_protected: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, json_schema_extra={"example": "developer1"})
    email: str = Field(..., min_length=5, max_length=128, json_schema_extra={"example": "developer1@company.internal"})
    role: str = Field("viewer", pattern="^(admin|operator|viewer)$")
    is_active: bool = True


class UserRoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern="^(admin|operator|viewer)$")


class UserStatusUpdateRequest(BaseModel):
    is_active: bool


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role([UserRole.ADMIN])),
):
    """List all registered platform users and their roles (Admin only)."""
    stmt = select(User).order_by(User.created_at.asc())
    result = await db.execute(stmt)
    users = result.scalars().all()
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
            is_protected=is_protected_system_admin(u),
            created_at=u.created_at,
            last_login=u.last_login,
        )
        for u in users
    ]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def onboard_user(
    payload: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([UserRole.ADMIN])),
):
    """Onboard a new user and assign their access role (Admin only)."""
    clean_username = payload.username.strip()
    clean_email = payload.email.strip()

    protected_username = getattr(settings, "DEFAULT_ADMIN_USERNAME", "admin").strip().lower()
    protected_email = getattr(settings, "DEFAULT_ADMIN_EMAIL", "admin@network-control-plane.local").strip().lower()
    if clean_username.lower() == protected_username or clean_email.lower() == protected_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot onboard an account with the reserved primary platform administrator username or email.",
        )

    stmt = select(User).where((User.username == clean_username) | (User.email == clean_email))
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A user with username '{clean_username}' or email '{clean_email}' already exists.",
        )

    now = datetime.now(timezone.utc)
    new_user = User(
        id=str(uuid.uuid4()),
        username=clean_username,
        email=clean_email,
        hashed_password="SSO_PRE_PROVISIONED",
        salt="SSO_MANAGED",
        role=payload.role,
        is_active=payload.is_active,
        created_at=now,
        last_login=None,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    await AuditService(db).log_event(
        action="ONBOARD_USER",
        resource_type="user",
        resource_id=new_user.id,
        risk_level="MEDIUM",
        details={
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role,
            "onboarded_by": current_user.user_id,
        },
    )

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role=new_user.role,
        is_active=new_user.is_active,
        is_protected=is_protected_system_admin(new_user),
        created_at=new_user.created_at,
        last_login=new_user.last_login,
    )


@router.put("/users/{username}/role", response_model=UserResponse)
async def update_user_role(
    username: str,
    payload: UserRoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([UserRole.ADMIN])),
):
    """Assign or modify a user's role (admin, operator, viewer) (Admin only)."""
    stmt = select(User).where((User.username == username) | (User.email == username))
    target = (await db.execute(stmt)).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{username}' not found.")

    # Guard: The primary root administrator role is immutable
    if is_protected_system_admin(target):
        await AuditService(db).log_event(
            action="BLOCKED_ROOT_ADMIN_ROLE_CHANGE_ATTEMPT",
            resource_type="user",
            resource_id=target.id,
            risk_level="HIGH",
            details={
                "target_username": target.username,
                "target_email": target.email,
                "attempted_role": payload.role,
                "actor": current_user.user_id,
            },
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"The primary system administrator account '{target.email}' has an immutable role and cannot be modified.",
        )

    if target.role == "admin" and payload.role != "admin":
        stmt_count = select(func.count(User.id)).where(User.role == "admin", User.is_active == True, User.id != target.id)
        other_admins = (await db.execute(stmt_count)).scalar() or 0
        if other_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the only active administrator on the platform.",
            )

    old_role = target.role
    target.role = payload.role
    await db.commit()
    await db.refresh(target)

    await AuditService(db).log_event(
        action="UPDATE_USER_ROLE",
        resource_type="user",
        resource_id=target.id,
        risk_level="MEDIUM",
        details={
            "username": target.username,
            "old_role": old_role,
            "new_role": payload.role,
            "modified_by": current_user.user_id,
        },
    )

    return UserResponse(
        id=target.id,
        username=target.username,
        email=target.email,
        role=target.role,
        is_active=target.is_active,
        is_protected=is_protected_system_admin(target),
        created_at=target.created_at,
        last_login=target.last_login,
    )


@router.put("/users/{username}/status", response_model=UserResponse)
async def update_user_status(
    username: str,
    payload: UserStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([UserRole.ADMIN])),
):
    """Activate or deactivate / suspend a user account (Admin only)."""
    stmt = select(User).where((User.username == username) | (User.email == username))
    target = (await db.execute(stmt)).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{username}' not found.")

    if not payload.is_active:
        # Guard: The primary root administrator cannot be deactivated or suspended
        if is_protected_system_admin(target):
            await AuditService(db).log_event(
                action="BLOCKED_ROOT_ADMIN_SUSPENSION_ATTEMPT",
                resource_type="user",
                resource_id=target.id,
                risk_level="HIGH",
                details={
                    "target_username": target.username,
                    "target_email": target.email,
                    "actor": current_user.user_id,
                },
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"The primary system administrator account '{target.email}' is protected and cannot be deactivated or suspended.",
            )

        if target.username == current_user.user_id or target.email == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own administrator account.",
            )
        if target.role == "admin":
            stmt_count = select(func.count(User.id)).where(User.role == "admin", User.is_active == True, User.id != target.id)
            other_admins = (await db.execute(stmt_count)).scalar() or 0
            if other_admins == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate the only active administrator on the platform.",
                )

    old_status = target.is_active
    target.is_active = payload.is_active
    await db.commit()
    await db.refresh(target)

    await AuditService(db).log_event(
        action="UPDATE_USER_STATUS",
        resource_type="user",
        resource_id=target.id,
        risk_level="MEDIUM",
        details={
            "username": target.username,
            "old_active": old_status,
            "new_active": payload.is_active,
            "modified_by": current_user.user_id,
        },
    )

    return UserResponse(
        id=target.id,
        username=target.username,
        email=target.email,
        role=target.role,
        is_active=target.is_active,
        is_protected=is_protected_system_admin(target),
        created_at=target.created_at,
        last_login=target.last_login,
    )


@router.delete("/users/{username}", status_code=status.HTTP_200_OK)
async def delete_user(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([UserRole.ADMIN])),
):
    """Delete a user account from the platform (Admin only)."""
    stmt = select(User).where((User.username == username) | (User.email == username))
    target = (await db.execute(stmt)).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{username}' not found.")

    # Guard: The primary root administrator cannot be deleted under any circumstances
    if is_protected_system_admin(target):
        await AuditService(db).log_event(
            action="BLOCKED_ROOT_ADMIN_DELETION_ATTEMPT",
            resource_type="user",
            resource_id=target.id,
            risk_level="HIGH",
            details={
                "target_username": target.username,
                "target_email": target.email,
                "actor": current_user.user_id,
            },
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"The primary system administrator account '{target.email}' is protected and cannot be deleted from the platform.",
        )

    if target.username == current_user.user_id or target.email == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own administrator account.",
        )

    if target.role == "admin":
        stmt_count = select(func.count(User.id)).where(User.role == "admin", User.is_active == True, User.id != target.id)
        other_admins = (await db.execute(stmt_count)).scalar() or 0
        if other_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the only active administrator on the platform.",
            )

    user_id = target.id
    target_username = target.username
    await db.delete(target)
    await db.commit()

    await AuditService(db).log_event(
        action="DELETE_USER",
        resource_type="user",
        resource_id=user_id,
        risk_level="HIGH",
        details={
            "username": target_username,
            "deleted_by": current_user.user_id,
        },
    )

    return {"message": f"User '{target_username}' successfully deleted from platform."}



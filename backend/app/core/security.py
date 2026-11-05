import json
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Connection

from app.db.datasource import data_source
from app.core.config import settings
from app.services.identity import IdentityService, UserContext

_firebase_app=None
bearer_scheme=HTTPBearer(
    scheme_name="FirebaseBearerAuth",
    description="Firebase ID token. Enter the token only; Swagger adds the Bearer prefix.",
    auto_error=False,
)

def verify_token(token:str)->dict:
    global _firebase_app
    if not settings.firebase_service_account_json:
        raise HTTPException(503,"Firebase authentication is not configured. Set FIREBASE_SERVICE_ACCOUNT_JSON on the backend.")
    try:
        import firebase_admin
        from firebase_admin import auth, credentials
        if not firebase_admin._apps:
            cred=credentials.Certificate(json.loads(settings.firebase_service_account_json))
            firebase_admin.initialize_app(cred, {"projectId":settings.firebase_project_id})
        return auth.verify_id_token(token, check_revoked=True)
    except HTTPException: raise
    except Exception as exc: raise HTTPException(401,"Invalid or expired Firebase token") from exc

def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_dev_user: str | None = Header(default=None),
    db: Connection = Depends(data_source.get_connection),
) -> UserContext:
    identity = IdentityService(db)
    if settings.dev_auth_bypass and x_dev_user:
        return identity.by_dev_email(x_dev_user)
    if not credentials:
        raise HTTPException(401,"Sign in required")
    claims=verify_token(credentials.credentials)
    try:
        return identity.by_firebase_claims(claims)
    except ValueError as exc:
        raise HTTPException(401,"Invalid or expired Firebase token") from exc

def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Connection = Depends(data_source.get_connection),
) -> UserContext | None:
    if not credentials:
        return None
    claims=verify_token(credentials.credentials)
    return IdentityService(db).optional_by_firebase_claims(claims)

def require_roles(*roles):
    def checker(user: UserContext = Depends(current_user)) -> UserContext:
        if not set(user.roles).intersection(roles):
            raise HTTPException(403,"Insufficient permissions")
        return user
    return checker

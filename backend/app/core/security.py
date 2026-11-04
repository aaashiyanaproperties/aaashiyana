import json
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User, UserRole
from app.core.config import settings

_firebase_app=None
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

def current_user(authorization:str|None=Header(default=None), x_dev_user:str|None=Header(default=None), db:Session=Depends(get_db)) -> User:
    if settings.dev_auth_bypass and x_dev_user:
        user=db.query(User).filter(User.email==x_dev_user).first()
        if not user:
            user=User(email=x_dev_user,full_name="Local development user")
            db.add(user); db.flush(); db.add(UserRole(user_id=user.id,role="seller")); db.commit(); db.refresh(user)
        return user
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401,"Sign in required")
    claims=verify_token(authorization.split(" ",1)[1])
    uid=claims.get("uid")
    user=db.query(User).filter(User.firebase_uid==uid).first()
    if not user:
        user=User(firebase_uid=uid,email=claims.get("email"),phone=claims.get("phone_number"),full_name=claims.get("name") or "Aashiyana user",avatar_url=claims.get("picture"))
        db.add(user); db.flush(); db.add(UserRole(user_id=user.id,role="buyer")); db.commit(); db.refresh(user)
    return user

def optional_user(authorization:str|None=Header(default=None), db:Session=Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "): return None
    claims=verify_token(authorization.split(" ",1)[1]); return db.query(User).filter(User.firebase_uid==claims.get("uid")).first()

def require_roles(*roles):
    def checker(user:User=Depends(current_user), db:Session=Depends(get_db)):
        user_roles={r.role for r in user.roles}
        if not user_roles.intersection(roles): raise HTTPException(403,"Insufficient permissions")
        return user
    return checker

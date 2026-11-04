import argparse
from app.db.session import SessionLocal
from app.models import User,UserRole,AuditLog

def main():
    parser=argparse.ArgumentParser(description="Grant admin role to an existing Aashiyana user")
    parser.add_argument("email")
    args=parser.parse_args(); db=SessionLocal()
    try:
        user=db.query(User).filter(User.email==args.email).first()
        if not user: raise SystemExit("User not found. Sign in once first so Firebase provisions the account.")
        if not db.query(UserRole).filter_by(user_id=user.id,role="admin").first(): db.add(UserRole(user_id=user.id,role="admin"))
        db.add(AuditLog(actor_id=user.id,action="admin.role.granted",entity_type="user",entity_id=user.id,metadata_json={"email":args.email}))
        db.commit(); print(f"Admin role granted to {args.email}")
    finally: db.close()
if __name__=="__main__": main()

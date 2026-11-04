import argparse
from app.db.session import SessionLocal
from app.models import User,UserRole
p=argparse.ArgumentParser();p.add_argument('email');a=p.parse_args();db=SessionLocal()
try:
 u=db.query(User).filter_by(email=a.email).first()
 if not u: raise SystemExit('User not found')
 db.query(UserRole).filter_by(user_id=u.id,role='admin').delete();db.commit();print('Admin role revoked')
finally: db.close()

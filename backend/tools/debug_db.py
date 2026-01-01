from database import SessionLocal
from models_db import User

db = SessionLocal()
u = db.query(User).filter(User.email == 'tsmluky@gmail.com').first()
if u:
    print(f"EMAIL: {u.email}")
    print(f"CREATED_AT: {u.created_at}")
    print(f"TYPE: {type(u.created_at)}")
else:
    print("User not found")
db.close()

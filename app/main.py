from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal
from app.model import Base, User

app = FastAPI()

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "E-Commerce Backend is running"}


@app.post("/users")
def create_user(
    name: str,
    email: str,
    db: Session = Depends(get_db)
):
    user = User(name=name, email=email)

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return {"message": "User not found"}

    return user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return {"message": "User not found"}

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}

@app.put("/users/{user_id}")
def update_user(
    user_id: int,
    name: str,
    email: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return {"message": "User not found"}

    user.name = name
    user.email = email

    db.commit()
    db.refresh(user)

    return user
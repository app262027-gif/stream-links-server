import os
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = "my-secret-key-123"
api_key_header = APIKeyHeader(name="x-api-key")

async def verify_api_key(key: str = Depends(api_key_header)):
    if key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key غلط!",
        )
    return key

# ✅ جدول قاعدة البيانات
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    password: str
    mode: str

class UserCredentials(BaseModel):
    username: str
    password: str
    mode: str

# ✅ إعداد قاعدة البيانات
sqlite_url = "sqlite:///users.db"
engine = create_engine(sqlite_url)

def create_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

@app.on_event("startup")
def on_startup():
    create_db()

# ✅ حفظ يوزر جديد
@app.post("/generate/", dependencies=[Depends(verify_api_key)])
async def save_credentials(data: UserCredentials, session: Session = Depends(get_session)):
    user = User(username=data.username, password=data.password, mode=data.mode)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": "تم الحفظ بنجاح", "username": user.username}

# ✅ جلب كل اليوزرات
@app.get("/users/", dependencies=[Depends(verify_api_key)])
async def get_all_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

# ✅ حذف يوزر
@app.delete("/users/{username}", dependencies=[Depends(verify_api_key)])
async def delete_user(username: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="اليوزر مو موجود!")
    session.delete(user)
    session.commit()
    return {"message": "تم الحذف بنجاح"}
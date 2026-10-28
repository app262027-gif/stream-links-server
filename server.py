import json
import os
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

class UserCredentials(BaseModel):
    username: str
    password: str
    mode: str

SAVE_FILE = "users.json"

def load_users():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return []

def save_users(users):
    with open(SAVE_FILE, "w") as f:
        json.dump(users, f, indent=2)

@app.post("/generate/", dependencies=[Depends(verify_api_key)])
async def save_credentials(data: UserCredentials):
    users = load_users()
    users.append(data.dict())
    save_users(users)
    return {"message": "تم الحفظ بنجاح", "username": data.username}

@app.get("/users/", dependencies=[Depends(verify_api_key)])
async def get_all_users():
    return load_users()

# ✅ endpoint جديد للحذف
@app.delete("/users/{username}", dependencies=[Depends(verify_api_key)])
async def delete_user(username: str):
    users = load_users()
    new_users = [u for u in users if u["username"] != username]
    if len(new_users) == len(users):
        raise HTTPException(status_code=404, detail="اليوزر مو موجود!")
    save_users(new_users)
    return {"message": "تم الحذف بنجاح"}
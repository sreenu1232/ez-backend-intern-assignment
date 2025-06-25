# File: main.py
# main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from typing import List
import shutil, os, uuid
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
fernet_key = os.getenv("FERNET_KEY").encode()
fernet = Fernet(fernet_key)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

users_db = {}
files_db = {}
download_tokens = {}

class User(BaseModel):
    email: EmailStr
    password: str
    role: str
    is_verified: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str

class FileMeta(BaseModel):
    id: str
    filename: str
    uploader: str
    uploaded_at: datetime

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return users_db.get(payload.get("sub"))
    except JWTError:
        return None

def get_current_user(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

@app.get("/")
def root():
    return RedirectResponse(url="/docs")

@app.post("/signup")
def signup(user: User):
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    user.password = pwd_context.hash(user.password)
    users_db[user.email] = user
    token = fernet.encrypt(user.email.encode()).decode()
    return {"message": "Signup successful", "verification_url": f"/verify-email/{token}"}

@app.get("/verify-email/{token}")
def verify_email(token: str):
    try:
        email = fernet.decrypt(token.encode()).decode()
        if email not in users_db:
            raise HTTPException(status_code=400, detail="Invalid token")
        users_db[email].is_verified = True
        return {"message": "Email verified"}
    except:
        raise HTTPException(status_code=400, detail="Invalid token")

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/upload")
def upload_file(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    if user.role != 'ops':
        raise HTTPException(status_code=403, detail="Only Ops can upload")
    ext = os.path.splitext(file.filename)[1]
    if ext not in [".docx", ".pptx", ".xlsx"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    file_id = str(uuid.uuid4())
    os.makedirs("uploads", exist_ok=True)
    with open(f"uploads/{file_id}_{file.filename}", "wb") as f:
        shutil.copyfileobj(file.file, f)
    files_db[file_id] = FileMeta(id=file_id, filename=file.filename, uploader=user.email, uploaded_at=datetime.utcnow())
    return {"message": "File uploaded"}

@app.get("/list-files")
def list_files(user: User = Depends(get_current_user)):
    if user.role != 'client' or not user.is_verified:
        raise HTTPException(status_code=403, detail="Only verified clients allowed")
    return list(files_db.values())

@app.get("/download-file/{file_id}")
def generate_download_link(file_id: str, user: User = Depends(get_current_user)):
    if user.role != 'client' or not user.is_verified:
        raise HTTPException(status_code=403, detail="Access denied")
    if file_id not in files_db:
        raise HTTPException(status_code=404, detail="File not found")
    token = fernet.encrypt(file_id.encode()).decode()
    download_tokens[token] = {"user": user.email, "file_id": file_id}
    return {"download-link": f"/secure-download/{token}", "message": "success"}

@app.get("/secure-download/{token}")
def secure_download(token: str, user: User = Depends(get_current_user)):
    try:
        data = download_tokens[token]
        if data["user"] != user.email:
            raise HTTPException(status_code=403, detail="Access denied")
        file_meta = files_db.get(data["file_id"])
        if not file_meta:
            raise HTTPException(status_code=404, detail="File not found")
        path = f"uploads/{file_meta.id}_{file_meta.filename}"
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(path, media_type="application/octet-stream", filename=file_meta.filename)
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    except:
        raise HTTPException(status_code=500, detail="Unexpected error")
@app.get("/download-history")
def download_history(user: User = Depends(get_current_user)):
    if user.role != 'client' or not user.is_verified:
        raise HTTPException(status_code=403, detail="Access denied")
    return [{"file_id": file_meta.id, "filename": file_meta.filename, "downloaded_at": datetime.utcnow()} for file_meta in files_db.values()]                   
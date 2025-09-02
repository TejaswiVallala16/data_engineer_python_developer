from dotenv import load_dotenv
from bson import ObjectId
import os, re
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo import MongoClient
from fastapi import FastAPI, HTTPException, Depends, status

# -------------------
# JWT CONFIG
# -------------------
load_dotenv()
SECRET_KEY = os.getenv("SECRETE_KEY")   # 🔴 use os.getenv in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["books_db"]
collection = db["books"]
users = db["users"]  # new collection for users
# FastAPI app
app = FastAPI(title="Books API with JWT Auth", version="1.2")


# -------------------
# Utility Functions
# -------------------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    """Decode JWT and return username"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception
    

# -------------------
# Auth Endpoints
# -------------------
@app.post("/register")
def register(username: str, password: str):
    """Register a new user"""
    if users.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_pw = get_password_hash(password)
    users.insert_one({"username": username, "password": hashed_pw})
    return {"message": "✅ User registered successfully"}


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and return JWT token"""
    user = users.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/books")
def get_books(page: int = 1, limit: int = 10, user: str = Depends(get_current_user)):
    """Get paginated books (requires JWT)"""
    skip = (page - 1) * limit
    books_cursor = collection.find().skip(skip).limit(limit)
    books = list(books_cursor)
    for b in books:
        b["_id"] = str(b["_id"])
    return {"user": user, "books": books}


@app.get("/books/search")
def search_books(q: str, page: int = 1, limit: int = 10, user: str = Depends(get_current_user)):
    """Search books by title (requires JWT)"""
    skip = (page - 1) * limit
    query = {"title": {"$regex": re.compile(q, re.IGNORECASE)}}
    books_cursor = collection.find(query).skip(skip).limit(limit)
    books = list(books_cursor)
    for b in books:
        b["_id"] = str(b["_id"])
    return {"query": q, "user": user, "books": books}


@app.get("/books/{book_id}")
def get_book(book_id: str):
    """
    Get a single book by its MongoDB _id
    """
    try:
        obj_id = ObjectId(book_id)  # convert string -> ObjectId
    except:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    book = collection.find_one({"_id": obj_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Convert _id back to string for JSON response
    book["_id"] = str(book["_id"])
    return book


@app.get("/categories")
def get_categories():
    """Get list of unique categories"""
    categories = collection.distinct("category")
    return {"categories": categories}
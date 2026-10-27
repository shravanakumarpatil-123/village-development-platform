"""
The actual app: wires all the routers together and starts the server.
Run this with: uvicorn app.main:app --reload
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.routers import auth, community, personal, agriculture, govservices, healthcare

app = FastAPI(title="Village Development Platform API")

# Allows your React frontend (running on a different port) to call this API
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# Serves uploaded complaint photos back out, e.g. /uploads/complaints/3_ab12cd.jpg
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

app.include_router(auth.router)
app.include_router(community.router)
app.include_router(personal.router)
app.include_router(agriculture.router)
app.include_router(govservices.router)
app.include_router(healthcare.router)


@app.get("/")
def root():
    return {"status": "Village Development Platform API is running"}

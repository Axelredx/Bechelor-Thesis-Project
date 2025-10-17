from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mongoengine import connect, get_db
from datetime import datetime
import os
from routers import classifier, asker, type_descriptor

app = FastAPI()

# Lettura variabili d'ambiente Docker
MONGO_HOST = os.getenv("MONGO_HOST", "my_mongodb")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "admin")
MONGO_PASS = os.getenv("MONGO_PASS", "password123")
MONGO_DB   = os.getenv("MONGO_DB", "test")

# Connessione a MongoDB
try:
    connect(
        db=MONGO_DB,
        host=MONGO_HOST,
        port=MONGO_PORT,
        username=MONGO_USER,
        password=MONGO_PASS,
        authentication_source="admin",
        alias="default"
    )
    db = get_db()
except Exception as e:
    raise e
# CORS per il frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",  # frontend container on Docker
        "http://localhost:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# router
app.include_router(classifier.router)
app.include_router(asker.router)
app.include_router(type_descriptor.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

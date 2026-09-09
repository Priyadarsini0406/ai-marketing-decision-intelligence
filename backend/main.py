from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from database.connection import Base, engine
from database import models

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    yield
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Marketing Decision Intelligence API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Marketing Decision Intelligence API"}

from api import leads, analytics, budget
from api import auth, admin
from api import datasets
from api import workspace

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(datasets.router)
app.include_router(workspace.router)

app.include_router(leads.router, dependencies=[Depends(auth.current_user)])
app.include_router(analytics.router, dependencies=[Depends(auth.current_user)])
app.include_router(budget.router, dependencies=[Depends(auth.current_user)])


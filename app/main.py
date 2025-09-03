# uvicorn app.main:app --reload
# uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
# gunicorn -k uvicorn.workers.UvicornWorker main:app --workers 4 --bind 0.0.0.0:8000
# docker build -t blog-app .
# docker run -p 8000:8000 blog-app
# docker run -p 8000:8000 -e DATABASE_URL=external_url blog-app

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from . import models
from . import auth
from . import comment
from . import post
from .database import engine
from .auth import get_db, get_current_user
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging

logging.basicConfig(level=logging.DEBUG)

# Check if tables exist before creating them
inspector = inspect(engine)
if not inspector.has_table("users"):
    models.Base.metadata.create_all(bind=engine)
else:
    print("Tables already exist. Skipping table creation.")

app = FastAPI()

app.include_router(auth.router)
app.include_router(comment.router)
app.include_router(post.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    posts = db.query(models.Post).all()
    return templates.TemplateResponse(
        "index.html", {"request": request, "posts": posts, "current_user": current_user}
    )

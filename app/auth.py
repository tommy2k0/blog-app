from fastapi import APIRouter, Form, Request, Response, Depends, Cookie, HTTPException
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from .database import SessionLocal
from .models import User
from .models import Session as UserSession
from .utils import hash_password, verify_password

router = APIRouter()

sessions = {}

templates = Jinja2Templates(directory="app/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(session_id: str = Cookie(None), db: Session = Depends(get_db)):
    if not session_id:
        # raise HTTPException(
        #     status_code=status.HTTP_401_UNAUTHORIZED, detail="No session cookie"
        # )
        return None

    db_session = (
        db.query(UserSession).filter(UserSession.session_id == session_id).first()
    )
    if not db_session:
        # raise HTTPException(
        #     status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
        # )
        return None

    return db_session.user


@router.get("/signup")
def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup", response_class=RedirectResponse)
def signup(
    username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)
):
    if db.query(User).filter(User.username == username).first():
        return {"error": "Username already exists"}
    new_user = User(username=username, password=hash_password(password))
    db.add(new_user)
    db.commit()
    return login(username=username, password=password, db=db)
    #return RedirectResponse(url="/posts/html", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=RedirectResponse)
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    session_id = str(uuid.uuid4())
    new_session = UserSession(
        session_id=session_id, username=username, created_at=datetime.utcnow()
    )
    db.add(new_session)
    db.commit()
    #response.set_cookie("session_id", session_id, httponly=True)  # max_age=3600
    redirect = RedirectResponse(url="/posts/html", status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie("session_id", session_id, httponly=True)  # max_age=3600
    return redirect

@router.get("/logout", response_class=RedirectResponse)
def logout_form(request: Request, response: Response, session_id: str = Cookie(None), db: Session = Depends(get_db)):
    return logout(response, session_id, db)

@router.post("/logout", response_class=RedirectResponse)
def logout(
    response: Response, session_id: str = Cookie(None), db: Session = Depends(get_db)
):
    if session_id:
        db.query(UserSession).filter(UserSession.session_id == session_id).delete()
        db.commit()
        response.delete_cookie("session_id")
    return RedirectResponse(url="/posts/html", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/me")
def read_current_user(user: User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"id": user.id, "username": user.username}

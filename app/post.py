from fastapi import APIRouter, Depends, Request, Form, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import SessionLocal, get_db
from .models import Post, User, Comment
from .models import Session as UserSession
from .auth import get_current_user
from .schemas import PostCreate, PostResponse

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/posts/create", response_class=HTMLResponse)
def create_post_form(request: Request):
    return templates.TemplateResponse("post_create.html", {"request": request})


@router.post("/posts/create", response_model=PostResponse)
def create_post(
    title: str = Form(...),
    content: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_post = Post(title=title, content=content, author_id=user.id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return HTMLResponse(
        f"Post '{new_post.title}' created! <a href='/posts/html'>Back to posts</a>"
    )


@router.get("/posts", response_model=list[PostResponse])
def list_posts_api(db: Session = Depends(get_db)):
    posts = db.query(Post).all()
    return posts


@router.get("/posts/html", response_class=HTMLResponse)
def list_posts_html(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    posts = list_posts_api(db)
    return templates.TemplateResponse(
        "index.html", {"request": request, "posts": posts, "current_user": current_user}
    )

@router.get("/posts/{post_id}", response_class=HTMLResponse)
def get_post(
    post_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = db.query(Comment).filter(Comment.post_id == post_id).all()
    return templates.TemplateResponse(
        "post_detail.html",
        {
            "request": request,
            "post": post,
            "current_user": current_user,
            "comments": comments,
        },
    )

@router.get("/posts/{post_id}/edit", response_class=HTMLResponse)
def edit_post_form(
    request: Request,
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this post")
    return templates.TemplateResponse("post_edit.html", {"request": request, "post": post, "current_user": current_user})


@router.put("/posts/{post_id}", response_model=PostResponse)
def edit_post(
    post_id: int,
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    if db_post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this post")
    db_post.title = post.title
    db_post.content = post.content
    db.commit()
    db.refresh(db_post)
    return db_post

@router.post("/posts/{post_id}/edit", response_class=RedirectResponse)
def edit_post_redirect(
    post_id: int,
    title: str = Form(...),
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post_data = PostCreate(title=title, content=content)
    updated_post = edit_post(post_id, post_data, current_user, db)
    return RedirectResponse(f"/posts/{updated_post.id}", status_code=303)

@router.delete("/posts/{post_id}", response_model=PostResponse)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post.")
    db.delete(post)
    db.commit()
    return post

@router.post("/posts/{post_id}/delete", response_class=RedirectResponse)
def delete_post_redirect(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delete_post(post_id, current_user, db)
    return RedirectResponse("/posts/html", status_code=303)
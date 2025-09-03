from fastapi import APIRouter, Depends, Request, HTTPException, Form, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import SessionLocal, get_db
from .models import Comment, User, Post
from .auth import get_current_user
from .schemas import CommentCreate, CommentResponse

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
def get_comments(post_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter_by(post_id=post_id).all()
    return comments


@router.get("/comments/{comment_id}", response_model=CommentResponse)
def get_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
def create_comment_api(
    post_id: int,
    content: CommentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    new_comment = Comment(**content.model_dump(), post_id=post_id, author_id=user.id)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


@router.post("/posts/{post_id}/comments/html", response_class=RedirectResponse)
def create_comment_html(
    post_id: int,
    content: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    new_comment = create_comment_api(
        post_id=post_id, content=CommentCreate(content=content), user=user, db=db
    )
    return RedirectResponse(
        url=f"/posts/{post_id}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/posts/{post_id}/comments/{comment_id}", response_model=CommentResponse)
def get_comment_by_post_api(
    post_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.get(
    "/posts/{post_id}/comments/{comment_id}/html", response_class=RedirectResponse
)
def get_comment_by_post_html(
    request: Request,
    post_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = get_comment_by_post_api(post_id, comment_id, db)
    return templates.TemplateResponse(
        "comment_details.html", {"request": request, "comment": comment, "current_user": current_user}
    )


@router.get("/comments/{comment_id}/edit", response_class=HTMLResponse)
def edit_comment_html(
    request: Request,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = get_comment(comment_id, db)
    return templates.TemplateResponse(
        "comment_edit.html", {"request": request, "comment": comment, "current_user": current_user}
    )


@router.put("/comments/{comment_id}", response_model=CommentResponse)
def edit_comment_api(
    comment_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this comment"
        )

    comment.content = comment_data.content
    db.commit()
    db.refresh(comment)
    return comment


@router.post("/comments/{comment_id}/edit", response_class=RedirectResponse)
def edit_comment_redirect(
    comment_id: int,
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = edit_comment_api(
        comment_id, CommentCreate(content=content), current_user, db
    )
    return RedirectResponse(
        url=f"/posts/{comment.post_id}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.delete("/comments/{comment_id}", response_model=CommentResponse)
def delete_comment_api(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this comment"
        )

    db.delete(comment)
    db.commit()
    return comment


@router.post("/comments/{comment_id}/delete", response_class=RedirectResponse)
def delete_comment_html(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = delete_comment_api(comment_id, current_user, db)
    return RedirectResponse(
        url=f"/posts/{comment.post_id}", status_code=status.HTTP_303_SEE_OTHER
    )

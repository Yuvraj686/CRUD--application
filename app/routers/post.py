from typing import List, Optional
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from .. import models, schemas, utils, oauth2
from sqlalchemy.orm import session, joinedload 
from sqlalchemy import  func
# from vote import vote
from ..database import get_db\

router = APIRouter(
    prefix="/posts",
    tags=['Posts']
)


# @router.get("/",response_model=List[schemas.Post])
@router.get("/",response_model=List[schemas.PostOut])
def get_posts(db: session = Depends(get_db),user_id: int = Depends(oauth2.get_current_user),Limit: int = 10,skip:int = 0,search: Optional[str] = ""):
    # cursor.execute("SELECT * FROM posts")
    # posts = cursor.fetchall()
    # print(Limit)
    result = db.query(models.Post,func.count(models.Vote.post_id).label("votes")).filter(models.Post.title.contains
    (search)).join(models.Vote,models.Post.id == models.Vote.post_id,isouter=True).group_by(models.Post.id).limit(Limit).offset(skip).all()
    return result


@router.post("/", status_code=status.HTTP_201_CREATED,response_model=schemas.Post)
def create_post(post: schemas.CreatePost, db: session = Depends(get_db),current_user:int 
                = Depends(oauth2.get_current_user)):
    # new_post = cursor.execute("""INSERT INTO posts(title,content,published) Values(%s,%s,%s) RETURNING * """,(post.title,post.content,post.published)) 
    # new_post = cursor.fetchone()
    # conn.commit()
    # print(current_user.id)
    new_post = models.Post(owner_id = current_user.id, **post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

# @router.get("/{id}",response_model=schemas.Post)
@router.get("/{id}",response_model=schemas.PostOut)
def get_post(id: int, db: session = Depends(get_db),current_user: int = Depends(oauth2.get_current_user)):
    # cursor.execute("""SELECT * FROM posts WHERE ID = %s""",str((id),))
    # post = cursor.fetchone()
    result = db.query(models.Post,func.count(models.Vote.post_id).label("votes")
    ).filter(models.Post.id == id).join(models.Vote,models.Post.id == models.Vote.post_id,isouter=True).group_by(models.Post.id).first()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"The post with id {id} was not found")
    
    return result   

@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: session = Depends(get_db),current_user: int = Depends(oauth2.get_current_user)):
    # cursor.execute("""DELETE FROM posts WHERE ID = %s RETURNING *""",str((id),))
    # deleted_post = cursor.fetchone()
    # conn.commit()
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"post with id: {id} does not exist")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform the requested action")
    post_query.delete(synchronize_session = False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{id}",response_model=schemas.Post) 
def update_post(id: int, updated_post: schemas.CreatePost, db: session = Depends(get_db),current_user = Depends(oauth2.get_current_user)):
    # cursor.execute("""UPDATE posts SET title = %s, content = %s,published = %s WHERE ID = %s RETURNING *""",(post.title,post.content,post.published,str((id),)))
    # updated_post = cursor.fetchone()
    # conn.commit()
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"post with id: {id} does not exist")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform the requested action")
    post_query.update(updated_post.dict(),synchronize_session = False)
    db.commit()
    return post_query.first()

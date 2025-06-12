from typing import Optional
from db import Session
from models.comment import Comment, CreateCommentModel, CommentModel
from sqlalchemy import select


def create(data: CreateCommentModel) -> CommentModel:
    with Session() as session:
        comment = Comment(**data.model_dump())
        session.add(comment)
        session.commit()
        return CommentModel.model_validate(comment)


def get(comment_id: int) -> Optional[CommentModel]:
    with Session() as session:
        comment = session.get(Comment, comment_id)
        return CommentModel.model_validate(comment) if comment else None


def get_by_product(product_type: str) -> list[CommentModel]:
    with Session() as session:
        comments = (
            session.execute(select(Comment).where(Comment.product_type == product_type))
            .scalars()
            .all()
        )
        return [CommentModel.model_validate(comment) for comment in comments]


def get_by_product_id(product_id: str) -> list[CommentModel]:
    with Session() as session:
        comments = (
            session.execute(select(Comment).where(Comment.product_id == product_id))
            .scalars()
            .all()
        )
        return [CommentModel.model_validate(comment) for comment in comments]


def delete(comment_id: int) -> int:
    with Session() as session:
        delete_count = session.query(Comment).filter(Comment.id == comment_id).delete()
        session.commit()
        return delete_count


def get_all() -> list[CommentModel]:
    with Session() as session:
        comments = session.execute(select(Comment)).scalars().all()
        return [CommentModel.model_validate(comment) for comment in comments]

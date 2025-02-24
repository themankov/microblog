from typing import Optional
from datetime import datetime, timezone
import sqlalchemy.orm as so
import sqlalchemy as sa
from app import db

class User(db.Model):
    id:so.Mapped[int]=so.mapped_column(primary_key=True)
    username:so.Mapped[str]=so.mapped_column(sa.String(64), unique=True, index=True)
    email:so.Mapped[str]=so.mapped_column(sa.String(120), unique=True, index=True)
    password_hash:so.Mapped[Optional[str]]=so.mapped_column(sa.String(128), unique=True, index=True)
    posts:so.Mapped[list['Post']]=so.relationship(
        'Post', back_populates='author',
    )

    def __repl__(self):
        return f'<{self.username}>'

class Post(db.Model):
    id:so.Mapped[int]=so.mapped_column(primary_key=True)
    body:so.Mapped[str]=so.mapped_column(sa.String(120))
    timestap:so.Mapped[datetime]=so.mapped_column(index=True, default=lambda:datetime.now(timezone.utc))
    user_id:so.Mapped[int]=so.mapped_column(sa.ForeignKey(User.id))
    author:so.Mapped[User]=so.relationship(back_populates='posts')

    def __repl__(self):
        return f'<{self.body}>'
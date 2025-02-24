from typing import Optional
from datetime import datetime, timezone
from hashlib import md5
import sqlalchemy.orm as so
import sqlalchemy as sa
from app import db
from flask_login import UserMixin
from app import login
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id:so.Mapped[int]=so.mapped_column(primary_key=True)
    username:so.Mapped[str]=so.mapped_column(sa.String(64), unique=True, index=True)
    email:so.Mapped[str]=so.mapped_column(sa.String(120), unique=True, index=True)
    password_hash:so.Mapped[Optional[str]]=so.mapped_column(sa.String(128), unique=True, index=True)
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc))
    posts:so.Mapped[list['Post']]=so.relationship(
        'Post', back_populates='author',
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'
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

@login.user_loader
def load_user(id):
  return db.session.get(User, int(id))
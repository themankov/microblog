from typing import Optional
from datetime import datetime, timezone
from hashlib import md5
import sqlalchemy.orm as so
import sqlalchemy as sa
from app import db
from flask_login import UserMixin
from app import login
from werkzeug.security import generate_password_hash, check_password_hash

followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True)
)
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
    following: so.Mapped[list['User']] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    followers: so.Mapped[list['User']] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        return len(self.followers)

    def following_count(self):
        return len(self.following)

    def following_posts(self):
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (
            sa.select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id,
            ))
            .group_by(Post)
            .order_by(Post.timestamp.desc())
        )

    def __repl__(self):
        return f'<{self.username}>'

class Post(db.Model):
    id:so.Mapped[int]=so.mapped_column(primary_key=True)
    body:so.Mapped[str]=so.mapped_column(sa.String(120))
    timestamp:so.Mapped[datetime]=so.mapped_column(index=True, default=lambda:datetime.now(timezone.utc))
    user_id:so.Mapped[int]=so.mapped_column(sa.ForeignKey(User.id))
    author:so.Mapped[User]=so.relationship(back_populates='posts')

    def __repl__(self):
        return f'<{self.body}>'

@login.user_loader
def load_user(id):
  return db.session.get(User, int(id))


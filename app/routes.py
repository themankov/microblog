from flask import render_template, redirect, flash, url_for, request
from urllib.parse import urlsplit
from datetime import datetime, timezone
from flask_login import current_user, login_user, logout_user, login_required
from app.forms import LoginForm, RegistrationForm, EditProfileForm,EmptyForm, PostForm
from app import app,db
import sqlalchemy as sa
from app.models import User,Post

@app.route('/login', methods=['GET', 'POST'])
def login():
  """
        Вход пользователя в систему

        Если пользователь уже вошел в систему, его перенаправляет на главную страницу.
        Если нет, отправляется форма входа по шаблону login.html
        При нажатии submit идет проверка:
        Если пользователя нет или пароль неверный перенаправляют на ту же страницу с сообщением через flash
        Если пользователь есть, то производят redirect на следующую страницу, взятую из аргументов
  """
  if current_user.is_authenticated:
    return redirect(url_for('index'))
  form = LoginForm()
  if form.validate_on_submit():
    user = db.session.scalar(
      sa.select(User).where(User.username == form.username.data))
    if user is None or not user.check_password(form.password.data):
      flash('Invalid username or password')
      return redirect(url_for('login'))
    login_user(user, remember=form.remember_me.data)
    next_page = request.args.get('next')
    if not next_page or urlsplit(next_page).netloc != '':
        next_page = url_for('index')
    return redirect(next_page)
  return render_template('login.html', title='Sign In', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
            Регистрация пользователя в системе

            Если пользователь уже вошел в систему, его перенаправляет на главную страницу.
            Если нет, отправляется форма регистрации по шаблону register.html
            При нажатии submit создается пользователь и выводится сообщение через flash
            Если пользователя нет или пароль неверный перенаправляют на ту же страницу с сообщением через flash
            Если пользователь есть, то производят redirect на следующую страницу, взятую из аргументов
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    """
                Главная страница

                Проверка на наличие авторизации
                Отправляем форму написания постов через шаблон index.html.
                При отправке поста он создается в бд, пользователь перенаправляется на эту же страницу и получает сообщение через flash
                Также учитывается пагинация для постов, номер страницы берется из аргументов запроса
        """
    page = request.args.get('page', 1, type=int)
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    posts = db.paginate(current_user.following_posts(), page=page,
                        per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    if posts.has_next:
        next_url = url_for('index', page=posts.next_num)
    else:
        next_url = None
    if posts.has_prev:
        prev_url = url_for('index', page=posts.prev_num)
    else:
        prev_url = None
    return render_template('index.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)
@app.route('/user/<username>')
@login_required
def user(username):
    """
                Просмотр страниц других пользователей

                Проверка на наличие авторизации
                Показ страницы пользователя по username
                Пагинация постов через страницы, номер которых берется из аргументов запроса
                Добавляем форму подписки на пользователя
        """
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts, form=form, next_url=next_url, prev_url=prev_url)

@app.before_request
def before_request():
    """
                 Функция обновлении времени перед каждым запросом

                 Если пользователь авторизован, то любой его запрос меняет его последнее время в сети
         """
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
                 Редактирование профиля

                 Проверка на наличие авторизации
                 Добавляем форму редактирования, пробрасывая внутрь наше имя для хранения состояния, через шаблон edit_profile.html
                 При отправке формы мы редиректим на эту же страницу и выводим сообщение через flash
         """
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)
@app.route('/logout')
def logout():
    """
                 Выход пользователя из системы

                 При выходе из системы редиректим на главную страницу
         """
    logout_user()
    return redirect(url_for('index'))

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    """
                 Подписка на пользователя

                 Проверка на наличие авторизации
                 Добавляем форму подписки на пользователя
                 Если форма успешно отправлена,то редирект на эту же страницу с сообщением через flash
    """
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are following {username}!')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    """
                 Отписка от пользователя

                 Проверка на наличие авторизации
                 Добавляем форму подписки на пользователя
                 Если форма успешно отправлена,то редирект на эту же страницу с сообщением через flash
    """
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are not following {username}.')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@app.route('/explore')
@login_required
def explore():
    """
                 Просмотр всех постов пользователей

                 Проверка на наличие авторизации
                 Пагинация постов через страницы, номер которых берется из аргументов запроса
         """
    page = request.args.get('page', 1, type=int)
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    if posts.has_next:
        next_url = url_for('index', page=posts.next_num)
    else:
        next_url = None
    if posts.has_prev:
        prev_url = url_for('index', page=posts.prev_num)
    else:
        prev_url = None
    return render_template("index.html", title='Explore', posts=posts.items, next_url=next_url,
                           prev_url=prev_url)
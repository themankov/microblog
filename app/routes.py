
from flask import render_template, redirect, flash, url_for
from app import forms
from app import app
@app.route('/login', methods=['GET', 'POST'])
def login():
    form=forms.LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)
@app.route('/index')
def index():
    user={'username':'Oleg'}
    posts=[{'author':{'name':'Anna'},'body':'Beautiful day in Portland!'},{'author':{'name':'Alex'},'body':'Bad day in Huvland!'}]
    return render_template('index.html', title='Home', user=user, posts=posts)
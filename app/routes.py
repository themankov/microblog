
from flask import render_template
from app import app
@app.route('/')
@app.route('/index')
def index():
    user={'username':'Oleg'}
    posts=[{'author':{'name':'Anna'},'body':'Beautiful day in Portland!'},{'author':{'name':'Alex'},'body':'Bad day in Huvland!'}]
    return render_template('index.html', title='Home', user=user, posts=posts)
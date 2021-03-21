from flask import (Blueprint, current_app, request,
                   session, flash, url_for, redirect, render_template,
                   g)
from functools import wraps
from passlib.hash import bcrypt
from service.cloud_logging import log_message

bp = Blueprint('auth', __name__, url_prefix="/")


def check_credentials(app, username, password):
    if app.config['ENV'] == 'GCLOUD':
        message = ("username in config: {} \n"
                   "password in config: {} \n"
                   "username provided: {} \n"
                   "password provided: {}\n".format(
            app.config['USERNAME'], app.config['PASSWORD'],
            username, password))
        log_message(message)

    if username != app.config['USERNAME']:
        return False
    elif not bcrypt.verify(password, app.config['PASSWORD']):
        return False
    return True


def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if g.user is not None:
            return func(*args, **kwargs)
        else:
            return redirect(url_for('auth.login'))

    return wrapper


@bp.route("/", methods=['GET', 'POST'])
def login():
    error = None
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if check_credentials(current_app,
                             request.form['username'],
                             request.form['password']):
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        else:
            error = "Invalid username\nor password"
    return render_template('login-page.html', error=error)


@bp.before_app_request
def load_user():
    username = session.get("username")
    if username is None:
        g.user = None
    else:
        g.user = username

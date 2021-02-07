from flask import (Blueprint, current_app, request,
                   session, flash, url_for, redirect, render_template,
                   g)
from functools import wraps

bp = Blueprint('auth', __name__, url_prefix="/")


def check_credentials(app, username, password):
    if username != app.config['USERNAME']:
        return False
    elif password != app.config['PASSWORD']:
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
    if request.method == "POST":
        try:
            username = request.form['username']
            password = request.form['password']
            print(check_credentials(current_app, username, password))
            if check_credentials(current_app,
                                 request.form['username'],
                                 request.form['password']):
                session['username'] = request.form['username']
            else:
                raise ValueError("Incorrect credentials")
            return redirect(url_for('upload.upload_files'))
        except KeyError:
            print("key error")
            flash("No username or password provided")
        except ValueError:
            print("value error")
            return render_template('login.html')
    return render_template('login.html')


@bp.before_app_request
def load_user():
    username = session.get("username")
    if username is None:
        g.user = None
    else:
        g.user = username



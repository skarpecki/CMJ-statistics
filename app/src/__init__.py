import os
from flask import Flask, request, flash, redirect, url_for, send_from_directory, render_template
# from werkzeug.utils import secure_filename
import app.src.stats_bp
import app.src.auth_bp

def check_extension(filename):
    return filename.rsplit('.', 1)[1].lower() == "csv"


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    upload_folder = r"D:\DevProjects\PythonProjects\CMJ-statistics\data\upload"
    app.config.from_mapping(
        SECRET_KEY='dev',
        UPLOAD_FOLDER=upload_folder,
        USERNAME='dev',
        PASSWORD='dev'
    )
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.register_blueprint(stats_bp.bp)
    app.register_blueprint(auth_bp.bp)

    return app


import os
import sys
from flask import Flask
# from werkzeug.utils import secure_filename
from blueprints import auth_bp
from blueprints import stats_bp

app = Flask(__name__)


def check_extension(filename):
    return filename.rsplit('.', 1)[1].lower() == "csv"


# def create_app(test_config=None):
app.config.from_object('EntryPoint.default_settings.DevelopmentConfig')

try:
    if os.environ.get("ENV") == 'GCLOUD':
        app.config["USERNAME"] = os.environ.get("USERNAME")
        app.config["PASSWORD"] = os.environ.get("PASSWORD")
        app.config["UPLOAD_FOLDER"] = os.environ.get("BUCKET")
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

    else:
        if os.environ.get("ENV") == "LOCAL":
            app.config.from_envvar('CMJ_SETTINGS')
            print("Settings from path loaded")
        os.makedirs(app.config.get('UPLOAD_FOLDER'), exist_ok=True)
        os.makedirs(r"{}\{}".format(app.config.get('UPLOAD_FOLDER'), "velocity"), exist_ok=True)
        os.makedirs(r"{}\{}".format(app.config.get('UPLOAD_FOLDER'), "force"), exist_ok=True)
except TypeError:
    print("No ENV variable provided - aborting program")
    sys.exit(2)
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

app.register_blueprint(auth_bp.bp, prefix='/')
app.register_blueprint(stats_bp.bp)


@app.errorhandler(500)
def server_error(e):
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0')

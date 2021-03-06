import os
import sys
from flask import Flask, render_template
import traceback


# from werkzeug.utils import secure_filename
from blueprints import auth_bp
from blueprints import upload_bp
from service.cloud_logging import log_message


app = Flask(__name__)


def check_extension(filename):
    return filename.rsplit('.', 1)[1].lower() == "csv"


# def create_app(test_config=None):


try:
    app.config["ENV"] = os.environ["ENV"]
    if os.environ["ENV"] == 'GCLOUD':
        app.config["USERNAME"] = os.environ["USERNAME"]
        app.config["PASSWORD"] = os.environ["PASSWORD"]
        app.config["UPLOAD_FOLDER"] = os.environ["BUCKET"]
        app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
        app.config["CMJ_COMP_URL"] = os.environ["CMJ_COMP_URL"]
        app.config["PROJECT_ID"] = os.environ["PROJECT_ID"]
        app.config["QUEUE_ID"] = os.environ["QUEUE_ID"]
        app.config["QUEUE_LOCATION"] = os.environ["QUEUE_LOCATION"]
    else:
        if os.environ["ENV"] == "LOCAL":
                app.config.from_envvar('CMJ_SETTINGS')
                app.config["CMJ_COMP_URL"] = os.environ["CMJ_COMP_URL"]
                print("Settings from path loaded")
        elif os.environ["ENV"] == "DEFAULT":
            app.config.from_object('EntryPoint.default_settings.DevelopmentConfig')
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(r"{}\{}".format(app.config['UPLOAD_FOLDER'], "velocity"), exist_ok=True)
        os.makedirs(r"{}\{}".format(app.config['UPLOAD_FOLDER'], "force"), exist_ok=True)
except TypeError:
    log_message(traceback.extract_stack())
    sys.exit(2)


try:
    os.makedirs(app.instance_path)
except OSError:
    pass

app.register_blueprint(auth_bp.bp, prefix='/')
app.register_blueprint(upload_bp.bp)


@app.route("/index")
def index():
    return render_template('index.html')


@app.errorhandler(500)
def server_error(e):
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0')

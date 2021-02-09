import os
from flask import Flask
# from werkzeug.utils import secure_filename
import cmj_stats_flask.src.bleuprints.auth_bp

def check_extension(filename):
    return filename.rsplit('.', 1)[1].lower() == "csv"


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('cmj_stats_flask.default_settings.DevelopmentConfig')
    if "CMJ_SETTINGS" in os.environ:
        app.config.from_envvar('CMJ_SETTINGS')
        print("Settings from path loaded")
    os.makedirs(app.config.get('UPLOAD_FOLDER'), exist_ok=True)
    os.makedirs(r"{}\{}".format(app.config.get('UPLOAD_FOLDER'), "velocity"), exist_ok=True)
    os.makedirs(r"{}\{}".format(app.config.get('UPLOAD_FOLDER'), "force"), exist_ok=True)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.register_blueprint(stats_bp.bp)
    app.register_blueprint(auth_bp.bp)

    @app.errorhandler(500)
    def server_error(e):
        return """
        An internal error occurred: <pre>{}</pre>
        See logs for full stacktrace.
        """.format(e), 500

    return app

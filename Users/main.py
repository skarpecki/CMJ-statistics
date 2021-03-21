from flask import Flask
from blueprints import users_bp

app = Flask(__name__.split()[0])

app.register_blueprint(users_bp.bp)


@app.errorhandler(500)
def server_error(e):
    return """Wrong data provided"""


if __name__ == "__main__":
    app.run(host="0.0.0.0")

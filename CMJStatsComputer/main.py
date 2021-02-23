from flask import Flask
import os


from blueprints.compute_bp import bp


app = Flask(__name__)


@app.route("/hello")
def hello():
    return "Hello World"


app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)

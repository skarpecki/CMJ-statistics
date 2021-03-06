from flask import Flask
import os
import sys
import traceback
from blueprints.compute_bp import bp
from service.cloud_logging import log_message

app = Flask(__name__)

app.register_blueprint(bp)


try:
    app.config["ENV"] = os.environ["ENV"]
    if os.environ["ENV"] == "GCLOUD":
        app.config["UPLOAD_FOLDER"] = os.environ["BUCKET"]
except TypeError:
    log_message(traceback.extract_stack())
    sys.exit(2)

@app.route("/test")
def test():
    return "Hello World!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)

from flask import Blueprint, request, redirect, make_response
import threading
import os

from service.thread_func import thread_func_gcloud
from service.cloud_logging import log_message

bp = Blueprint('cmj-compute', __name__)


@bp.route("/", methods=['POST'])
def compute():
    log_message("Computation start")
    athletes_files = request.get_json(force=True)

    # Threading this way doesnt work in GCP - to remember...
    # thread = threading.Thread(target=thread_func_gcloud, args=(athletes_files["filenames"]))
    # thread.start()
    # thread.join()

    thread_func_gcloud(athletes_files["filenames"])
    return "done"


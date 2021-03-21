from flask import Blueprint, current_app, request, redirect, render_template
from google.protobuf import timestamp_pb2
from google.cloud import tasks_v2
import requests
import json
import datetime
from collections import Counter
import datetime

from blueprints.auth_bp import require_auth
from service.cloud_logging import log_message
from service.upload import verify_files, upload_gcloud

bp = Blueprint('upload', __name__)


@bp.route("/", methods=('GET', 'POST'))
@require_auth
def upload_files():
    if request.method == 'POST':
        force_files = request.files.getlist("force[]")
        velocity_files = request.files.getlist("velocity[]")
        try:
            force_files, velocity_files = verify_files(force_files, velocity_files)
        except ValueError:
            return redirect(request.url)

        data = upload_gcloud(force_files, velocity_files)
        log_message(str(data))
        data = json.dumps(data)

        url = current_app.config["CMJ_COMP_URL"]
        headers = {'Content-Type': 'application/json'}

        # TODO: add some secret key to header so each request is verified by computations endpoint

        client = tasks_v2.CloudTasksClient()
        project = 'athletes-dashboard-306517'
        queue = 'athletes-dashboard'
        location = "europe-west1"
        parent = client.queue_path(project, location, queue)
        # str(datetime.utcnow()) return string with illegal characters for task's name like "-", ".", ":" etc.
        # (e.g '2021-02-27 17:01:23.864414'), hence following instructions removes those chars
        ch = ["-", " ", ":", "."]
        now = "".join(list(filter(lambda b: True if b not in ch else False, str(datetime.datetime.utcnow()))))
        task = {
            'name': 'projects/{}/locations/{}/queues/{}/tasks/{}'.format(project, location, queue, now),
            'http_request': {
                'http_method': tasks_v2.HttpMethod.POST,
                'headers': headers,
                'url': url,
                'body': data.encode(),
            }
        }
        in_seconds = 180
        d = datetime.datetime.utcnow() + datetime.timedelta(seconds=in_seconds)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(d)
        task['schedule_time'] = timestamp

        # response = requests.request("POST", url, headers=headers, data=data)
        # log_message("Request response: ".format(response.text))
        response = client.create_task(request={"parent": parent, "task": task})
        # response = client.create_task(parent=parent, task=task)
        log_message("Request {}: {} sent to url: {}".format(response.name, response.view, url))

        return render_template("upload-page.html")

    return render_template("upload-page.html")

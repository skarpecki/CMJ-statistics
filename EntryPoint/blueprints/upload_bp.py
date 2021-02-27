from flask import Blueprint, current_app, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import os
from google.cloud import storage
from google.protobuf import timestamp_pb2
from google.cloud import tasks_v2
import requests
import json
import datetime

from service.csv_name_parser import check_extension, parse_cmj_csv_name, sort_list
from blueprints.auth_bp import require_auth
from service.cloud_logging import log_message

bp = Blueprint('upload', __name__, url_prefix='/upload')


def upload_locally(force_files, velocity_files):
    """
    :param force_files: list of force fiels
    :param velocity_files: list of velocity files
    :return: dict of (filenames, path to force files, path to velocity files)
    """
    filenames = []
    force_path = os.path.abspath(current_app.config['UPLOAD_FOLDER'] + r"\force")
    velocity_path = os.path.abspath(current_app.config['UPLOAD_FOLDER'] + r"\velocity")
    for file in force_files:
        path = os.path.join(force_path, file.filename)
        file.save(path)
    for file in velocity_files:
        path = os.path.join(velocity_path, file.filename)
        file.save(path)
        filenames.append(file.filename)
    return {"filenames": filenames,
            "force": force_path,
            "velocity": velocity_path}


def remove_locally(filenames):
    for filename in list(filenames):
        os.remove(r"{}\velocity\{}".format(current_app.config['UPLOAD_FOLDER'], filename))
        os.remove(r"{}\force\{}".format(current_app.config['UPLOAD_FOLDER'], filename))


def upload_gcloud(force_files, velocity_files):
    storage_client = storage.Client()
    bucket = storage_client.bucket(current_app.config['UPLOAD_FOLDER'])

    filenames = []
    force_path = current_app.config['UPLOAD_FOLDER'] + r"/force"
    velocity_path = current_app.config['UPLOAD_FOLDER'] + r"/velocity"

    for file in force_files:
        blob = bucket.blob(r"force/{}".format(file.filename))
        blob.upload_from_file(file)

    for file in velocity_files:
        blob = bucket.blob(r"velocity/{}".format(file.filename))
        blob.upload_from_file(file)
        filenames.append(file.filename)

    return {"filenames": filenames,
            "force": force_path,
            "velocity": velocity_path}


@bp.route("/", methods=('GET', 'POST'))
@require_auth
def upload_files():
    if request.method == 'POST':
        velocity_files = request.files.getlist("velocity[]")
        force_files = request.files.getlist("force[]")
        filenames = []

        if len(velocity_files) != len(force_files):
            return redirect(request.url)
        if len(velocity_files) == 0 or len(force_files) == 0:
            return redirect(request.url)

        for file in force_files:
            if file and check_extension(file.filename):
                file.filename = secure_filename(file.filename)
                file.filename = parse_cmj_csv_name(file.filename)
            else:
                return redirect(request.url)
        for file in velocity_files:
            if file and check_extension(file.filename):
                file.filename = secure_filename(file.filename)
                file.filename = parse_cmj_csv_name(file.filename)
            else:
                redirect(request.url)
        filenames = sort_list(filenames)
        if current_app.config["ENV"] == "LOCAL" or current_app.config["ENV"] == "DEFAULT":
            data = upload_locally(force_files, velocity_files)
        elif current_app.config["ENV"] == "GCLOUD":
            data = upload_gcloud(force_files, velocity_files)
            log_message(str(data))
        data = json.dumps(data)

        url = current_app.config["CMJ_COMP_URL"]
        headers = {'Content-Type': 'application/json'}

        # TODO: add some secret key to header so each request is verified by computations endpoint

        client = tasks_v2.CloudTasksClient()
        project = 'cmj-stats'
        queue = 'CMJ-COMPUTE-QUEUE'
        location = "europe-west3"
        parent = client.queue_path(project, location, queue)
        # str(datetime.utcnow()) return string with illegal characters for task's name like "-", ".", ":" etc.
        # (e.g '2021-02-27 17:01:23.864414'), hence following instructions removes those chars
        ch = ["-", " ", ":", "."]
        now = "".join(list(filter(lambda b: True if b not in ch else False, str(datetime.datetime.utcnow()))))
        # url = 'https://cmj-stats-compute-dot-cmj-stats.ey.r.appspot.com/cmj/compute'
        task = {
            'name': 'projects/{}/locations/{}/queues/{}/tasks/{}'.format(project, location, queue, now),
            'app_engine_http_request': {
                'http_method': tasks_v2.HttpMethod.POST,
                'headers': headers,
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
        # response = client.create_task(request={"parent": parent, "task": task})
        response = client.create_task(parent=parent, task=task)
        # log_message("Request {}: {} sent to url: {}".format(response.name, response.view, url))

        return render_template("upload-page.html")

    return render_template("upload-page.html")

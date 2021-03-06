from flask import Blueprint, current_app, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import os
from google.cloud import storage
from google.protobuf import timestamp_pb2
from google.cloud import tasks_v2
import requests
import json
import datetime
from collections import Counter
import datetime

from blueprints.auth_bp import require_auth
from service.cloud_logging import log_message
from service.hawkin_csv_parser import CmjCsvFile, CmjCsvFilesList

bp = Blueprint('upload', __name__, url_prefix='/upload')


def upload_gcloud(force_files: CmjCsvFilesList, velocity_files: CmjCsvFilesList):
    storage_client = storage.Client()
    bucket = storage_client.bucket(current_app.config['UPLOAD_FOLDER'])

    now = datetime.datetime.now()
    now = "{}{}{}{}".format(now.hour, now.minute, now.second, now.microsecond)

    force_subdir = r"force/{}/".format(now)
    velocity_subdir = r"velocity/{}/".format(now)
    force_path = current_app.config['UPLOAD_FOLDER'] + force_subdir
    velocity_path = current_app.config['UPLOAD_FOLDER'] + velocity_subdir

    for csv_file in force_files.files_list:
        blob = bucket.blob(force_subdir + csv_file.csv_filename.filename)
        blob.upload_from_file(csv_file.file)

    for csv_file in velocity_files.files_list:
        blob = bucket.blob(velocity_subdir + csv_file.csv_filename.filename)
        blob.upload_from_file(csv_file.file)

    return {"filenames": velocity_files.filenames,
            "force_path": force_subdir,
            "velocity_path": velocity_subdir}


def verify_files(force_files: CmjCsvFilesList, velocity_files: CmjCsvFilesList):
    force_files = CmjCsvFilesList(force_files)
    velocity_files = CmjCsvFilesList(velocity_files)

    force_files.sort_list()
    velocity_files.sort_list()

    if len(velocity_files.files_list) != len(force_files.files_list):
        raise ValueError("Different number of velocity files and force_files")
    if len(velocity_files.files_list) == 0 or len(force_files.files_list) == 0:
        raise ValueError("No velocity or force files provided")

    force_files_counter = dict(Counter(force_files.files_list))
    velocity_files_counter = dict(Counter(force_files.files_list))

    log_message("Force: {}".format(str(force_files_counter)))
    log_message("Velocity: {}".format(str(velocity_files_counter)))

    if force_files_counter != velocity_files_counter:
        raise ValueError("Different velocity and force files provided")

    return force_files, velocity_files


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
        project = current_app.config["PROJECT_ID"]
        queue = current_app.config["QUEUE_ID"]
        location = current_app.config["QUEUE_LOCATION"]
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

from flask import Blueprint, current_app, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import os
from google.cloud import storage
import requests
import json

from service.csv_name_parser import check_extension, parse_cmj_csv_name, sort_list
from blueprints.auth_bp import require_auth
from service.logging import log_message

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

    message = ("Force files type: {} \n"
               "Velocity fiels type: {}".format(type(force_files), type(velocity_files)))
    log_message(message)

    for file in force_files:
        message = ("Force file type: {} \n".format(type(file)))
        log_message(message)
        blob = bucket.blob(r"force/{}".format(file.filename))
        blob.upload_from_file(file)
        filenames.append(file.filename)

    for file in velocity_files:
        blob = bucket.blob(r"velocity/{}".format(file.filename))
        blob.upload_from_file(file)


@bp.route("/", methods=('GET', 'POST'))
@require_auth
def upload_files():
    if request.method == 'POST':
        velocity_files = request.files.getlist("velocity[]")
        force_files = request.files.getlist("force[]")
        filenames = []
        force_files_dict = {}
        velocity_files_dict = {}
        dict_athletes = {}

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

        data = upload_locally(force_files, velocity_files)
        data = json.dumps(data)
        url = current_app.config["CMJ_COMP_URL"]
        # TODO: add some secret key to header so each request is verified by computations endpoint
        headers = {'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, data=data)
        print(response.text)

        return render_template("upload-page.html")

    return render_template("upload-page.html")

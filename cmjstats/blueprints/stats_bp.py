from flask import Blueprint, current_app, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import os
from google.cloud import storage

from service.csv_parser import check_extension, parse_cmj_csv_name, sort_list
import service.cmj_stats as cmj_stats
from blueprints.auth_bp import require_auth
from service.logging import log_message

bp = Blueprint('upload', __name__, url_prefix='/upload')


def upload_locally(force_files, velocity_files):
    filenames = []
    for file in force_files:
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'] + r"\force", file.filename))
        filenames.append(file.filename)
    for file in velocity_files:
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'] + r"\velocity", file.filename))
    return filenames


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
                filenames.append(file.filename)
                force_files_dict[file.filename] = file
            else:
                return redirect(request.url)
        for file in velocity_files:
            if file and check_extension(file.filename):
                file.filename = secure_filename(file.filename)
                file.filename = parse_cmj_csv_name(file.filename)
                velocity_files_dict[file.filename] = file
            else:
                redirect(request.url)
        filenames = sort_list(filenames)

        force_headers = {"time": "Time (s)", "left": "Left (N)", "right": "Right (N)",
                         "combined": "Combined (N)"}
        velocity_headers = {"time": "Time (s)", "velocity": "Velocity (M/s)"}
        for filename in filenames:
            cmj_force_attr = cmj_stats.CMJAttribute(force_files_dict[filename], force_headers)
            cmj_vel_attr = cmj_stats.CMJAttribute(velocity_files_dict[filename], velocity_headers)
            cmj = cmj_stats.CMJForceVelStats(cmj_vel_attr, cmj_force_attr, "Time (s)")
            dict_cmj = cmj.get_cmj_stats()
            dict_athletes[filename.split('.')[0]] = dict_cmj

        return render_template("show_stats.html", dict_athletes=dict_athletes)

    return render_template("upload-page.html")

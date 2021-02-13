from flask import Blueprint, current_app, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import os

from cmj_stats_flask.src.service.csv_parser import check_extension, parse_cmj_csv_name, sort_list
import cmj_stats_flask.src.service.cmj_stats as cmj_stats
from cmj_stats_flask.src.controllers.auth_bp import require_auth


bp = Blueprint('upload', __name__, url_prefix='/upload')


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

        # saving files after checking all stuff

        for file in force_files:
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'] + r"\force", file.filename))
            filenames.append(file.filename)
        for file in velocity_files:
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'] + r"\velocity", file.filename))
        return redirect(url_for('upload.stats', filenames=sort_list(filenames)))
    return render_template("upload-page.html")


@bp.route("/stats")
@require_auth
def stats():
    filenames = request.args.getlist("filenames")
    dict_athletes = {}
    try:
        for filename in list(filenames):
            cmj_vel_attr = cmj_stats.CMJAttribute(r"{}\velocity\{}".format(current_app.config['UPLOAD_FOLDER'], filename),
                                                  {"time": "Time (s)", "velocity": "Velocity (M/s)"})
            cmj_force_attr = cmj_stats.CMJAttribute(r"{}\force\{}".format(current_app.config['UPLOAD_FOLDER'], filename),
                                                    {"time": "Time (s)", "left": "Left (N)", "right": "Right (N)",
                                                     "combined": "Combined (N)"})
            cmj = cmj_stats.CMJForceVelStats(cmj_vel_attr, cmj_force_attr, "Time (s)")
            dict_cmj = cmj.get_cmj_stats()
            dict_athletes[filename.split('.')[0]] = dict_cmj
    except ValueError:
        return redirect(url_for('upload.upload_files'))
    finally:
        for filename in list(filenames):
            os.remove(r"{}\velocity\{}".format(current_app.config['UPLOAD_FOLDER'], filename))
            os.remove(r"{}\force\{}".format(current_app.config['UPLOAD_FOLDER'], filename))
    return render_template("show_stats.html", dict_athletes=dict_athletes)

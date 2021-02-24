from flask import Blueprint, request, redirect
import threading
import os

from service.cmj_stats import VelocityCMJAttribute, ForceCMJAttribute, CMJForceVelStats

bp = Blueprint('cmj-compute', __name__, url_prefix='/cmj/compute')


def compute_thread(filenames: list, vel_file_path: str, force_file_path: str):
    for filename in filenames:
        vel_path = r"{}\{}".format(vel_file_path, filename)
        force_path = r"{}\{}".format(force_file_path, filename)
        with open(vel_path) as vel_csv_file:
            cmj_vel_attr = VelocityCMJAttribute(vel_csv_file)
        with open(force_path) as force_csv_file:
            cmj_force_attr = ForceCMJAttribute(force_csv_file)
        cmj = CMJForceVelStats(cmj_vel_attr, cmj_force_attr, "Time (s)")
        stats = cmj.get_cmj_stats()
        print(stats)
        os.remove(vel_path)
        os.remove(force_path)


@bp.route("/", methods=['POST'])
def compute():
    athletes_files = request.get_json(force=True)
    thread = threading.Thread(target=compute_thread, args=(athletes_files["filenames"],
                                                           athletes_files["velocity"],
                                                           athletes_files["force"]))
    thread.start()

    """
    for file_path in athletes_files.values():
        if not os.path.isfile():
            return redirect(request.url, code=404)
    """
    print("Computing files")
    return "computed fine "

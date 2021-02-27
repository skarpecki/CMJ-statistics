import os
from service.cmj_stats import VelocityCMJAttribute, ForceCMJAttribute, CMJForceVelStats
from google.cloud import storage
from flask import current_app
import tempfile
from service.cloud_logging import log_message


def thread_func_local(filenames: list, vel_file_path: str, force_file_path: str):
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


def thread_func_gcloud(filenames: list):
    log_message("thread func")
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(current_app.config["UPLOAD_FOLDER"])
    for filename in filenames:
        blob = storage.Blob("force/{}".format(filename), bucket)
        with tempfile.TemporaryFile() as tf:
            storage_client.download_blob_to_file(blob, tf)
            tf.seek(0)
            cmj_force_attr = ForceCMJAttribute(tf)
        blob = bucket.blob(r"velocity/{}".format(filename))
        with tempfile.TemporaryFile() as tf:
            storage_client.download_blob_to_file(blob, tf)
            tf.seek(0)
            cmj_vel_attr = VelocityCMJAttribute(tf)
        blob = bucket.blob(r"stats/{}".format(filename))
        cmj = CMJForceVelStats(cmj_vel_attr, cmj_force_attr, "Time (s)")
        stats = cmj.get_cmj_stats()
        with tempfile.TemporaryFile(mode="w+t") as tf:
            tf.write(str(stats))
            tf.seek(0)
            blob.upload_from_file(tf)
        log_message(str(stats))

import os
from service.cmj_stats import VelocityCMJAttribute, ForceCMJAttribute, CMJForceVelStats
from google.cloud import storage
from flask import current_app
import tempfile
from service.cloud_logging import log_message


def thread_func_gcloud(filenames: list[str], force_subdir: str, velocity_subdir: str):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(current_app.config["UPLOAD_FOLDER"])
    for filename in filenames:
        blob = storage.Blob("{}{}".format(force_subdir, filename), bucket)
        with tempfile.TemporaryFile() as tf:
            storage_client.download_blob_to_file(blob, tf)
            tf.seek(0)
            cmj_force_attr = ForceCMJAttribute(tf)
        blob.delete()
        blob = bucket.blob(r"{}{}".format(velocity_subdir, filename))
        with tempfile.TemporaryFile() as tf:
            storage_client.download_blob_to_file(blob, tf)
            tf.seek(0)
            cmj_vel_attr = VelocityCMJAttribute(tf)
        blob.delete()
        blob = bucket.blob(r"stats/{}".format(filename))
        cmj = CMJForceVelStats(cmj_vel_attr, cmj_force_attr, "Time (s)")
        stats = cmj.get_cmj_stats()
        with tempfile.TemporaryFile(mode="w+t") as tf:
            tf.write(str(stats))
            tf.seek(0)
            blob.upload_from_file(tf)
        log_message(str(stats))

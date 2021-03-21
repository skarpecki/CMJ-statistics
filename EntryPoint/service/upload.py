from flask import current_app
from google.cloud import storage
import datetime
from collections import Counter

from service.hawkin_csv_parser import CmjCsvFile, CmjCsvFilesList
from service.cloud_logging import log_message

def upload_gcloud(force_files: CmjCsvFilesList, velocity_files: CmjCsvFilesList):
    storage_client = storage.Client()
    bucket = storage_client.bucket(current_app.config['UPLOAD_FOLDER'])

    now = datetime.datetime.now()
    now = "{}{}{}{}".format(now.hour, now.minute, now.second, now.microsecond)
    force_path = current_app.config['UPLOAD_FOLDER'] + r"force/{}/".format(now)
    velocity_path = current_app.config['UPLOAD_FOLDER'] + r"velocity/{}/".format(now)

    for csv_file in force_files.files_list:
        blob = bucket.blob(force_path + csv_file.csv_filename.filename)
        blob.upload_from_file(csv_file.file)

    for csv_file in velocity_files.files_list:
        blob = bucket.blob(velocity_path + csv_file.csv_filename.filename)
        blob.upload_from_file(csv_file.file)

    return {"filenames": velocity_files.filenames,
            "force_path": force_path,
            "velocity_path": velocity_path}


def verify_files(force_files: CmjCsvFilesList, velocity_files: CmjCsvFilesList):
    force_files = CmjCsvFilesList(force_files)
    velocity_files = CmjCsvFilesList(velocity_files)

    # force_files.sort_list()
    # velocity_files.sort_list()

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


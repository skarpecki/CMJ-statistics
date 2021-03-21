from google.cloud import datastore
from model.Athlete import Athlete
import datetime


def insert_athlete(data: dict, json_srvc_account=None):
    if json_srvc_account is not None:
        client = datastore.Client.from_service_account_json(json_srvc_account)
    else:
        client = datastore.Client()
    kind = "Athlete"
    athlete_ent = datastore.Entity(client.key(kind))
    athlete = Athlete.create_from_dict(data)
    athlete_ent.update(athlete.get_datastore_dict())
    client.put(athlete_ent)


def get_athletes(json_srvc_account=None, **kwargs):
    """

    :param json_srvc_account: path to json service account details
    :param kwargs: fields of Athlete class
    :return: list of object of Athlete class
    """
    if json_srvc_account is not None:
        client = datastore.Client.from_service_account_json(json_srvc_account)
    else:
        client = datastore.Client()
    kind = "Athlete"
    query = client.query(kind=kind)
    for key, value in kwargs.items():
        query.add_filter(key, "=", value)
    athletes = []
    for elem in list(query.fetch()):
        athletes.append(Athlete.create_from_dict(elem))
    return athletes


if __name__ == "__main__":
    json_path = r"D:\DevProjects\PythonProjects\CMJ-statistics\Test-Scripts\Athletes Dashboard-e5e75a707f35.json"
    d1 = {"first_name": "Rosbin",
          "last_name": "Volkmar",
          "coaches": ["kkruczek", "pzeromski"]
          }
    a2 = Athlete.create_from_dict(d1)
    print(a2)
    insert_athlete(d1, json_srvc_account=json_path)

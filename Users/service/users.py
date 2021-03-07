from google.cloud import datastore
from model.Athlete import  Athlete
import datetime


def insert_athlete(athlete: Athlete, json_srvc_account=None):
    if json_srvc_account is not None:
        client = datastore.Client.from_service_account_json(json_srvc_account)
    else:
        client = datastore.Client()
    kind = "Athlete"
    athlete_ent = datastore.Entity(client.key(  kind))
    athlete_ent.update(athlete.get_datastore_dict())
    client.put(athlete_ent)


if __name__ == "__main__":
    a1 = Athlete("Bartek", "Karpecki", ["kkruczek"], birthdate=datetime.date(1998, 2, 15))
    insert_athlete(a1, r"D:\DevProjects\PythonProjects\CMJ-statistics\Test-Scripts\Athletes Dashboard-e5e75a707f35.json")

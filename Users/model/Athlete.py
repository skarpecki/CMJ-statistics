import datetime
from google.cloud.datastore import Entity
import json


class Athlete:
    birthdate_format = "%Y-%m-%d"

    def __init__(self, first_name, last_name, coaches=[], **kwargs):
        self.first_name = first_name
        self.last_name = last_name
        self.coaches = coaches
        self.birthdate = kwargs.get('birthdate')
        self.sport = kwargs.get('sport')
        if self.birthdate is not None:
            self.age = Athlete.calc_age(self.birthdate)

    @property
    def birthdate(self):
        return self._birthdate

    @birthdate.setter
    def birthdate(self, birthdate):
        self._birthdate = birthdate

    @staticmethod
    def calc_age(birthdate):
        curr_date = datetime.datetime.now().date()
        year_diff = curr_date.year - birthdate.year
        if curr_date.month > birthdate.month:
            return year_diff
        elif curr_date.month == birthdate.month and curr_date.day >= birthdate.day:
            return year_diff
        else:
            return year_diff - 1

    def get_datastore_dict(self):
        athlete_dict = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            # "coaches": self.coaches,
            "sport": getattr(self, "sport", None)
        }
        birthdate = getattr(self, "birthdate")
        if birthdate is not None:
            athlete_dict["birthdate"] = birthdate.strftime(self.birthdate_format)
        else:
            athlete_dict["birthdate"] = None
        return athlete_dict

    @classmethod
    def create_from_dict(cls, data: dict):
        athlete = Athlete(
            first_name=data["first_name"],
            last_name=data["last_name"],
            # coaches=data.get("coaches") if data.get("coaches") is not None else None,
            # following are optional kwargs, hence using get which doesn't raise KeyError
            birthdate=datetime.datetime.strptime(data.get("birthdate"), cls.birthdate_format).date() if \
                data.get("birthdate") is not None else None,
            sport=data.get("sport") if data.get("sport") is not None else None
        )
        return athlete

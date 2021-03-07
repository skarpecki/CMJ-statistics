import datetime
from google.cloud.datastore import Entity


class Athlete:
    birthdate_format = "%d/%m/%y"

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
        if birthdate is not None:
            now = datetime.datetime.now().date()
            if now.year - birthdate.year >= 100:
                # constraint to make use of strtime/strptime - it returns same format for e.g 1905 and 2005 (year as 05)
                raise ValueError("Wrong birthdate - cannot set mor than 100 year ago")
            self._birthdate = birthdate
        else:
            self._birthdate = None

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
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "coaches": self.coaches,
            "birthdate": self.birthdate.strftime(self.birthdate_format),
            "sport": self.sport
        }

    @classmethod
    def create_from_entity(cls, entity: Entity):
        athlete = Athlete(
            first_name=entity["first_name"],
            last_name=entity["last_name"],
            coaches=entity["coaches"],
            # following are optional kwargs, hence using get which doesn't raise KeyError
            birthdate=datetime.datetime.strptime(entity.get("birthdate"), cls.birthdate_format).date(),
            sport=entity.get("sport")
        )
        return athlete




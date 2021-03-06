from copy import deepcopy
from datetime import date


class CmjCsvName:
    """Class that parses filename in format from Hawkin Dynamics force platform"""

    def __init__(self, filename: str):
        """
        :param filename: str in format of Hawkin Dynamics platform.
        """
        self.filename = CmjCsvName.parse_cmj_csv_name(filename)
        if not self._check_extension():
            raise ValueError("Provided file has wrong format")
        self.firstname = self.get_firstname()
        self.lastname = self.get_lastname()
        self.date = self.get_date()

    @classmethod
    def parse_cmj_csv_name(cls, filename):
        jump = filename.split('-')
        jump_athlete = jump[1].split('_')[0:2]
        jump_date = jump[2].split('_')[0:3]
        jump_athlete = "_".join(jump_athlete)
        jump_date = "_".join(jump_date)
        jump = "-".join((jump_athlete, jump_date))
        return jump + ".csv"

    def _check_extension(self):
        return self.filename.rsplit('.', 1)[1].lower() == "csv"

    def get_lastname(self):
        return self.filename.split("-")[0].split("_")[1]

    def get_firstname(self):
        return self.filename.split("-")[0].split("_")[0]

    def get_date(self):
        """us date format"""
        date_str = self.filename.split("-")[1].split(".")[0].split("_")
        return date(int(date_str[2]), int(date_str[0]), int(date_str[1]))

    def __repr__(self):
        return "CmjCsvName({})".format(self.filename)

    def __str__(self):
        return self.filename


class CmjCsvFile:
    """Class that represents file-like csv from Hawkin Dynamics """

    def __init__(self, _file):
        """
        :param _file: CSV Hawkin Dynamics file
        """
        self.file = _file
        # file from request hence using filename
        if getattr(self.file, "filename", None) is not None:
            self.csv_filename = CmjCsvName(getattr(self.file, "filename"))
        # file like object hence using name
        elif getattr(self.file, "name", None) is not None:
            self.csv_filename = CmjCsvName(getattr(self.file, "name"))
        else:
            raise TypeError("Wrong file type")


class CmjCsvFilesList:
    """List of CSV files from Hawking Dynamics"""

    def __init__(self, files_list=[]):
        """
        :param files_list: list of file like objects from Hawkin Dynamics
        """
        self.filenames = []
        self.files_list = []
        if files_list:
            for _file in files_list:
                csv_file = CmjCsvFile(_file)
                self.files_list.append(csv_file)
                self.filenames.append(csv_file.csv_filename.filename)

    def append(self, _file):
        csv_file = CmjCsvFile(_file)
        self.files_list.append(csv_file)
        self.filenames.append(csv_file.csv_filename.filename)

    def sort_list(self):
        athletes = self.files_list
        n = len(athletes)
        for i in range(n):
            for j in range(n - 1 - i):
                temp1 = athletes[j]
                temp2 = athletes[j + 1]

                if temp1.csv_filename.lastname > temp2.csv_filename.lastname:
                    athletes[j], athletes[j + 1] = athletes[j + 1], athletes[j]

        for i in range(n):
            for j in range(n - 1 - i):
                temp1 = athletes[j]
                temp2 = athletes[j + 1]
                if temp1.csv_filename.lastname == temp2.csv_filename.lastname \
                        and temp1.csv_filename.firstname > temp2.csv_filename.firstname:
                    athletes[j], athletes[j + 1] = athletes[j + 1], athletes[j]

        for i in range(n):
            for j in range(n - 1 - i):
                temp1 = athletes[j]
                temp2 = athletes[j + 1]

                if temp1.csv_filename.lastname == temp2.csv_filename.lastname \
                        and temp1.csv_filename.firstname == temp2.csv_filename.firstname \
                        and temp1.csv_filename.date > temp2.csv_filename.date:
                    athletes[j], athletes[j + 1] = athletes[j + 1], athletes[j]
        self.files_list = athletes

    def get_len(self):
        return len(self.files_list)


class MockFile:
    def __init__(self, filename):
        self.filename = filename


if __name__ == "__main__":
    athletess = [MockFile("Force-Robin_Volkmar_Countermovement_Jump-10_14_2020_07-00-26 2.csv"),
                 MockFile("Force-Adam_Lewandowski_Countermovement_Jump-10_14_2020_07-00-26 2.csv"),
                 MockFile("Force-Robin_Volkmar_Countermovement_Jump-10_14_2020_07-00-26 2.csv"),
                 MockFile("Force-Szymon_Karpecki_Countermovement_Jump-10_14_2020_07-00-26 2.csv"),
                 MockFile("Force-Robin_Volkmar_Countermovement_Jump-10_14_2020_07-00-26 2.csv"),
                 MockFile("Force-Bartlomiej_Karpecki_Countermovement_Jump-10_14_2020_07-00-26 2.csv"),
                 MockFile("Force-Adam_Lewandowski_Countermovement_Jump-10_14_2020_07-00-26 2.csv")]

    cmj_list = CmjCsvFilesList(athletess)
    cmj_list.sort_list()
    for file in cmj_list.files_list:
        s = file.csv_filename
        print(s)
    print(cmj_list.get_len())


    with open(
            r"C:\Users\Szymon\Desktop\data\force\Force-Adam_Lewandowski_Countermovement_Jump-10_14_2020_07-00-26 2.csv") as file:
        cmj_file = CmjCsvFile(file)
        print()
        print(cmj_file.csv_filename)

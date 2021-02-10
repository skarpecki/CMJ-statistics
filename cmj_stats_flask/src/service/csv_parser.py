from copy import deepcopy
from datetime import date


def parse_cmj_csv_name(filename):
    jump = filename.split('-')
    jump_athlete = jump[1].split('_')[0:2]
    jump_date = jump[2].split('_')[0:3]
    jump_athlete = "_".join(jump_athlete)
    jump_date = "_".join(jump_date)
    jump = "-".join((jump_athlete, jump_date))
    return jump + ".csv"


def check_extension(filename):
    return filename.rsplit('.', 1)[1].lower() == "csv"


def get_lastname(filename: str):
    return filename.split("-")[0].split("_")[1]


def get_firstname(filename: str):
    return filename.split("-")[0].split("_")[0]


def get_date(filename: str):
    """us date format"""
    date_str = filename.split("-")[1].split(".")[0].split("_")
    return date(int(date_str[2]), int(date_str[0]), int(date_str[1]))


# TODO: There must be more efficient way than bubble sort

def sort_list(list_athletes):
    athletes = deepcopy(list_athletes)
    n = len(athletes)
    for i in range(n):
        for j in range(n - 1 - i):
            temp1 = athletes[j]
            temp2 = athletes[j + 1]

            if get_lastname(temp1) > get_lastname(temp2):
                athletes[j], athletes[j + 1] = athletes[j + 1], athletes[j]

    for i in range(n):
        for j in range(n - 1 - i):
            temp1 = athletes[j]
            temp2 = athletes[j + 1]
            if get_lastname(temp1) == get_lastname(temp2) \
                    and get_firstname(temp1) > get_firstname(temp2):
                athletes[j], athletes[j + 1] = athletes[j + 1], athletes[j]

    for i in range(n):
        for j in range(n - 1 - i):
            temp1 = athletes[j]
            temp2 = athletes[j + 1]

            if get_lastname(temp1) == get_lastname(temp2) \
                    and get_firstname(temp1) == get_firstname(temp1) \
                    and get_date(temp1) > get_date(temp2):
                athletes[j], athletes[j + 1] = athletes[j + 1], athletes[j]
    return athletes


if __name__ == "__main__":
    athletess = ["Robin_Volkmar-01_20_2021",
                 "Robin_Volkmar-12_20_2020",
                 "Robin_Volkmar-11_20_2020",
                 "Robin_Volkmar-12_31_2020",
                 "Szymon_Karpecki-12_20_2020",
                 "Bartlomiej_Karpecki-12_20_2020",
                 "Adam_Lewandowski-01_01_2021"]
    from pprint import pprint as pp

    pp(sort_list(athletess))

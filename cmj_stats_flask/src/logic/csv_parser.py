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


# TODO: There must be more efficient way to do this

def sort_list(list_athletes):
    athletes = deepcopy(list_athletes)
    n = len(athletes)
    for i in range(n):
        for j in range(n - 1 - i):
            temp1 = athletes[j].split("-")
            temp2 = athletes[j + 1].split("-")

            temp1_surname = temp1[0].split("_")[1]
            temp2_surname = temp2[0].split("_")[1]

            if temp1_surname > temp2_surname:
                athletes[j], athletes[j + 1] = athletes[j + 1], athletes[j]

    for i in range(n):
        for j in range(n - 1 - i):
            temp1 = athletes[j].split("-")
            temp2 = athletes[j + 1].split("-")
            temp1_surname = temp1[0].split("_")[1]
            temp2_surname = temp2[0].split("_")[1]

            temp1_name = temp1[0].split("_")[0]
            temp2_name = temp2[0].split("_")[0]

            if temp1_surname == temp2_surname and temp1_name > temp2_name:
                athletes[j], athletes[j + 1] = athletes[j + 1], athletes[j]

    for i in range(n):
        for j in range(n - 1 - i):
            temp1 = athletes[j].split("-")
            temp2 = athletes[j + 1].split("-")
            temp1_surname = temp1[0].split("_")[1]
            temp2_surname = temp2[0].split("_")[1]
            temp1_name = temp1[0].split("_")[0]
            temp2_name = temp2[0].split("_")[0]

            temp1_date_str = temp1[1].split(".")[0].split("_")
            temp2_date_str = temp2[1].split(".")[0].split("_")

            temp1_date = date(int(temp1_date_str[2]), int(temp1_date_str[0]), int(temp1_date_str[1])) # us date format...
            temp2_date = date(int(temp2_date_str[2]), int(temp2_date_str[0]), int(temp2_date_str[1]))

            if temp1_surname == temp2_surname and temp1_name == temp2_name and temp1_date > temp2_date:
                athletes[j], athletes[j + 1] = athletes[j + 1], athletes[j]
    return athletes


if __name__ == "__main__":
    athletess = ["Robin_Volkmar-20_01_2021",
                 "Robin_Volkmar-20_12_2020",
                 "Robin_Volkmar-20_11_2020",
                 "Robin_Volkmar-31_12_2020",
                 "Szymon_Karpecki-20_12_2020",
                 "Bartlomiej_Karpecki-20_12_2020",
                 "Adam_Lewandowski-01_01_2021"]
    from pprint import pprint as pp

    pp(sort_list(athletess))

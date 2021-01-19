import pandas as pd
from csv import reader
from functools import partial, reduce


class CMJStats:
    def __init__(self, type_csv_path: dict, join_on: str, **headers):
        self.type_csv_path = type_csv_path
        self.headers = headers
        for key, item in type_csv_path.items():
            CMJStats._verify_csv_header(item, headers[key])  # will raise TypeError if any wrong
        self.df_base = self.create_base_df(join_on=join_on)
        self.g = 9.81
        self.system_weight = self.get_system_wght(self.df_base, "Combined (N)")

    @staticmethod
    def _verify_csv_header(csv_file_path: str, columns: list):
        """
        Verifies if csv file header contain
        all the columns from the arg columns list
        csv_file: path to file
        columns: list of columns names that needs to be present in csv file header
        """
        with open(csv_file_path, mode="rt") as csv_file:
            f_reader = reader(csv_file)
            headers = list(next(f_reader))
            for col in columns:
                if col not in headers:
                    raise ValueError("Wrong csv headers. No {} column.".format(col))

    def create_base_df(self, join_on):
        """
        Validates, cleans and merge dataframes created from csv files
        provided in type_csv_path dictionary as __init__ argument
        :param join_on: column on which dataframes should be joined
        :return:
        """
        df_dict = {}
        for key, item in self.type_csv_path.items():
            df_dict[key] = pd.read_csv(item)
            for col in self.headers[key]:
                if col not in df_dict[key]:
                    raise ValueError("{} column not present in {} file".format(col, key))
            # drop all columns that are not in headers list for file type
            df_dict[key] = df_dict[key][df_dict[key].columns.intersection(self.headers[key])]
        if len(df_dict.keys()) > 1:
            my_reduce = partial(pd.merge, on=join_on, how='inner')
            df_base = reduce(my_reduce, df_dict.values())
        else:
            df_base = df_dict.values()
        return df_base

    @staticmethod
    def get_system_wght(df_base, col_name):
        df = df_base.iloc[0:1000]
        return df[col_name].mean()

    def get_pos_vel_df(self, stamp: int):
        """
        Finds positive velocity dataframe from base dataframe provided to object
        :param stamp: timestamp from first positive velocity value for which dataframe needst to be created
        :return: tuple of pandas dataframe with data from first positive velocity + timestamp and timestamp
        """
        pos_vel_idx = -1
        for index, row in self.df_base.iterrows():
            if pos_vel_idx == -1 and row['Velocity (M/s)'] < 0:
                pos_vel_idx = 0
            if pos_vel_idx == 0 and row['Velocity (M/s)'] > 0:
                pos_vel_idx = index
                break
        df_pos_val = self.df_base.iloc[pos_vel_idx: pos_vel_idx + stamp]
        df_pos_val.reset_index(drop=True)
        for index, row in df_pos_val.iterrows():
            df_pos_val.loc[index, "Acceleration (M/s^2)"] = \
                (self.df_base.loc[index, "Velocity (M/s)"] - self.df_base.loc[index - 1, "Velocity (M/s)"]) \
                / (self.df_base.loc[index, "Time (s)"] - self.df_base.loc[index - 1, "Time (s)"])

        # stats = df_pos_val.describe()[["Velocity (M/s)", "Acceleration (M/s^2)"]]
        # stats = stats.loc[['mean', 'min', 'max']]

        return df_pos_val, stamp

    def create_pos_vel_excel(self, df_pos_val, stamp, path):
        """

        :param stamp: stamp for which excel should be created
        :param df_pos_val: dataframe containing positive velocity values
        :param path: path where workbook should be created

        :return:
        """
        stats = df_pos_val.describe()[["Velocity (M/s)", "Acceleration (M/s^2)"]].loc[['mean', 'min', 'max']]
        writer = pd.ExcelWriter(f"{path}\\{stamp}.xlsx", engine='xlsxwriter')
        df_pos_val.to_excel(writer, sheet_name=f"{stamp}_data")
        stats.to_excel(writer, sheet_name=f"{stamp}_stat")
        # df.to_excel(writer, sheet_name=f"source")

        workbook = writer.book
        worksheet = writer.sheets[f"{stamp}_data"]

        chart = workbook.add_chart({'type': 'scatter',
                                    'subtype': 'smooth'})
        chart.add_series({
            'name': 'v(t)',
            'categories': f'={stamp}_data!$B$2:$B$101',
            'values': f'={stamp}_data!$C$2:$C$101',
        })

        chart.add_series({
            'name': 'a(t)',
            'categories': f'={stamp}_data!$B$2:$B$101',
            'values': f'={stamp}_data!$D$2:$D$101',
            'y2_axis': 1,
        })

        chart.set_title({'name': 'CMJ'})
        chart.set_x_axis({'name': 'Time (s)'})
        chart.set_y_axis({'name': 'Velocity (m/s)'})
        chart.set_y2_axis({'name': "Acceleration (m/s^2)"})
        chart.set_size({'x_scale': 2, 'y_scale': 1.5})
        worksheet.insert_chart('H2', chart)

        writer.sheets[f"{stamp}_data"].set_column(1, 1, 10)
        writer.sheets[f"{stamp}_data"].set_column(2, 2, 15)
        writer.sheets[f"{stamp}_data"].set_column(3, 3, 20)

        writer.sheets[f"{stamp}_stat"].set_column(1, 1, 15)
        writer.sheets[f"{stamp}_stat"].set_column(2, 2, 20)

        # writer.sheets['source'].set_column(1, 1, 10)
        # writer.sheets['source'].set_column(2, 2, 15)

        writer.close()

    def get_stats(self, source_path):
        df_velocity = pd.read_csv(source_path + r"\velocity.csv")
        df_force = pd.read_csv(source_path + r"\force.csv")
        df_force = df_force[["Time (s)", "Left (N)", "Right (N)", "Combined (N)"]]
        for index, row in df_velocity.iterrows():
            if index == 0:
                df_velocity.loc[index, "Acceleration (m/s^2)"] = df_velocity.loc[index, "Velocity (M/s)"] / \
                                                                 df_velocity.loc[index, "Time (s)"]
            else:
                df_velocity.loc[index, "Acceleration (m/s^2)"] = (df_velocity.loc[index, "Velocity (M/s)"] -
                                                                  df_velocity.loc[index - 1, "Velocity (M/s)"]) / (
                                                                         df_velocity.loc[index, "Time (s)"] -
                                                                         df_velocity.loc[index - 1, "Time (s)"])

        df_all = df_velocity.merge(df_force, how="inner", on="Time (s)")

        ind_unwght_start = -1
        ind_unwght_end = -1
        ind_brk_start = -1
        ind_brk_end = -1
        ind_prop_start = -1
        ind_prop_end = -1

        for index, row in df_all.iterrows():
            # unweighting phase start
            if ind_unwght_start < 0 and row["Velocity (M/s)"] < 0:
                # check for next 50ms if velocity is below zero to get rid of noise of RLS type of athlete (mr. "boli
                # mnie dwojka" iks de)
                ind_unwght_start = index
                for i in range(50):
                    if df_all.loc[index + i, "Velocity (M/s)"] > 0:
                        ind_unwght_start = -1
                        break

            # braking phase start (a >= 0 after unweighting) a = 0 <==> Force equals to force in silent phase (weight
            # of athlete)
            if ind_unwght_start > 0 and ind_brk_start < 0:  # in unweighting phase (set ind) and ind_brk not set
                if row["Acceleration (m/s^2)"] >= 0:
                    ind_brk_start = index
                    # check for next 5ms so any noise won't be incldued
                    for i in range(50):
                        if df_all.loc[index + i, "Acceleration (m/s^2)"] < 0:
                            ind_brk_start = -1
                            break
                ind_unwght_end = ind_brk_start - 1

            if ind_brk_start > 0 and ind_prop_start < 0:
                if row['Velocity (M/s)'] >= 0:
                    ind_prop_start = index
                    for i in range(5):
                        if row['Velocity (M/s)'] < 0:
                            ind_prop_start = -1
                ind_brk_end = ind_prop_start - 1

            if ind_prop_start > 0 and ind_prop_end < 0:
                if row["Acceleration (m/s^2)"] < (-1 * self.g + 0.1):
                    ind_prop_end = index
                    for i in range(5):
                        if row["Acceleration (m/s^2)"] > (-1 * self.g + 0.2):
                            ind_prop_end = -1

        print(ind_unwght_start)
        print(ind_brk_start)
        print(ind_prop_start)
        print(ind_prop_end)
        print("\n\n\n")

        df_unwght = df_all.iloc[ind_unwght_start: ind_unwght_end]
        df_brk = df_all.iloc[ind_brk_start: ind_brk_end]
        df_prop = df_all.iloc[ind_prop_start: ind_prop_end]
        df_neg_vel = df_all.iloc[ind_unwght_start: ind_brk_end]
        df_pos_a = df_all.iloc[ind_brk_start: ind_prop_end]

        v_peak_prop = df_prop["Velocity (M/s)"].max()
        v_peak_prop_idx = df_prop["Velocity (M/s)"].idxmax()
        v_peak_neg = df_neg_vel["Velocity (M/s)"].min()
        v_peak_neg_idx = df_neg_vel["Velocity (M/s)"].idxmin()
        v_avg_neg = df_neg_vel["Velocity (M/s)"].mean()
        t_to_v_peak_prop = df_prop.loc[v_peak_prop_idx, "Time (s)"] - df_prop.loc[ind_prop_start, "Time (s)"]
        v_avg_100_prop = df_prop.loc[ind_prop_start: ind_prop_start + 100, "Velocity (M/s)"].mean()
        a_avg_100_prop = df_prop.loc[ind_prop_start: ind_prop_start + 100, "Acceleration (m/s^2)"].mean()
        a_peak_100_prop = df_prop.loc[ind_prop_start: ind_prop_start + 100, "Acceleration (m/s^2)"].max()
        v_peak_100_prop = df_prop.loc[ind_prop_start: ind_prop_start + 100, "Velocity (M/s)"].max()
        a_peak_pos = df_pos_a["Acceleration (m/s^2)"].max()

        print("Time to v peak pos:                      {:.4f} s".format(t_to_v_peak_prop))
        print("v peak pos:                              {:.4f} m/s".format(v_peak_prop))
        print("v peak neg:                             {:.4f} m/s".format(v_peak_neg))
        print("v avg 100ms pos:                        {:.4f} m/s".format(v_avg_100_prop))
        print("a avg 100ms prop:                       {:.4f} m/s^2".format(a_avg_100_prop))
        print("a peak 100ms prop:                       {:.4f} m/s^2".format(a_peak_100_prop))
        print("v peak 100ms prop:                       {:.4f} m/s^2".format(v_peak_100_prop))
        print("v peak neg /  Time to v peak pos:        {:.4f}".format(v_peak_neg / t_to_v_peak_prop))
        print("v peak neg / V peak prop:               {:.4f}".format(v_peak_neg / v_peak_prop))
        print("v avg neg / V peak prop:                {:.4f}".format(v_avg_neg / v_peak_prop))
        print("v avg neg / first 100 ms v pos avg:     {:.4f} ".format(v_avg_neg / v_avg_100_prop))
        print("v peak neg / first 100 ms v pos avg:    {:.4f}".format(v_peak_neg / v_avg_100_prop))
        print("v avg neg / first 100 ms acc prop avg:  {:.4f}".format(v_avg_neg / a_avg_100_prop))
        print("v peak neg / first 100 ms acc prop avg: {:.4f}".format(v_peak_neg / a_avg_100_prop))


if __name__ == "__main__":
    cmj = CMJStats(
        {"velocity": r"D:\DevProjects\PythonProjects\CMJ-statistics\app\src\velocity.csv",
         "force": r"D:\DevProjects\PythonProjects\CMJ-statistics\app\src\force.csv"},
        "Time (s)",
        velocity=["Time (s)", "Velocity (M/s)"],
        force=["Time (s)", "Left (N)", "Right (N)", "Combined (N)"]
    )
    # t = cmj.get_pos_vel_df(50)
    # print(t)
    # cmj.create_pos_vel_excel(t[0], t[1], r"C:\Users\Szymon\Desktop\test")
    cmj.get_stats(r"D:\DevProjects\PythonProjects\CMJ-statistics\app\src")

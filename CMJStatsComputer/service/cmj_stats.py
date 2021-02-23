import pandas as pd
from csv import reader
from functools import partial, reduce
from itertools import tee
import copy
import shutil


class CMJAttribute:
    """
    Objects of that class contain details of particular
    attribute/characteristic of counter movement, for
    example it would be velocity or force
    """

    def __init__(self, csv_file: 'file', headers: dict):
        """
        :param csv_path: path to csv file
        :param headers: dictionary with key as attribute (time, velocity, left, combined etc.) and col name as value
        """
        self.csv_file = csv_file
        self.headers = headers
        # self._verify_csv_header(csv_file)
        self._df = self.create_df()

    def _verify_csv_header(self, csv_file):
        """
        Verifies if csv file header contain
        all the columns from the arg columns list
        csv_file: path to file
        columns: list of columns names that needs to be present in csv file header
        """
        f_reader = copy.copy(reader(csv_file))
        headers_csv = list(next(f_reader))
        for col in list(self.headers.values()):
            if col not in headers_csv:
                raise ValueError("Wrong csv headers. No {} column.".format(col))

    @property
    def df(self):
        return self._df

    def create_df(self):
        """
        Generates dataframe from csv file provided as attribute of object
        :return: pandas dataframe with data from csv file
        """
        df = pd.read_csv(self.csv_file)
        df = df[df.columns.intersection(list(self.headers.values()))]
        return df


class ForceCMJAttribute(CMJAttribute):

    def __init__(self, csv_path, headers={"time": "Time (s)", "left": "Left (N)", "right": "Right (N)",
                                          "combined": "Combined (N)"}):
        super().__init__(csv_path, headers)


class VelocityCMJAttribute(CMJAttribute):
    """
    Velocity characteristic of counter movement jump.
    Inherits from CMJAttribute
    """

    def __init__(self, csv_path, headers={"time": "Time (s)", "velocity": "Velocity (M/s)"}):
        super().__init__(csv_path, headers)




class CMJForceVelStats:
    def __init__(self, vel_attr: CMJAttribute, force_attr: CMJAttribute, join_on: str, **kwargs):
        """
        :param type_csv_path: dictionary containing file type (velocity, force etc.) as key and path to file as value
        :param join_on: column on which joining should be performed between files
        :param kwargs:
            velocity: dictionary containing velocity file headers
            force: dictionary containig force file headers
        """
        self.vel_attr = vel_attr
        self.force_attr = force_attr
        self.df_base = pd.merge(vel_attr.df, force_attr.df, how="inner", on=join_on)
        self.g = 9.81
        self.system_weight = self.get_system_weight(self.df_base, force_attr.headers["combined"])

    @staticmethod
    def get_system_weight(df_base, col_name):
        """
        Calculates system weight as mean from first 1000 entries in force data
        :param df_base: dataframe containing both velocity and force or only force
        :param col_name: name of column which contains combined force
        :return: tuple of mean and standard deviation of calculations
        """
        df = df_base.iloc[0:1000]
        return df[col_name].mean(), df[col_name].std()

    @staticmethod
    def calculate_acceleration(df, time_interval, velocity_col):
        if time_interval > 0.01:
            raise ValueError("Time interval too small to safely interpolate first value")
        first = 0
        for index, row in df.iterrows():
            if first == 0:
                # assuming that first difference will be equal to average of next 3 differences
                vel_diff = ((df.loc[index + 3, velocity_col] - df.loc[index + 2, velocity_col]) +
                            (df.loc[index + 2, velocity_col] - df.loc[index + 1, velocity_col]) +
                            (df.loc[index + 1, velocity_col] - df.loc[index, velocity_col])) / 3
                df.loc[index, "Acceleration (m/s^2)"] = vel_diff / time_interval
                first += 1
            else:
                df.loc[index, "Acceleration (m/s^2)"] = (
                        (df.loc[index, velocity_col] - df.loc[index - 1, velocity_col]) / time_interval)
        return df

    def get_phases_idx(self):
        ind_unwght_start = -1
        ind_unwght_end = -1
        ind_brk_start = -1
        ind_brk_end = -1
        ind_prop_start = -1
        ind_prop_end = -1
        force_col = self.force_attr.headers["combined"]
        vel_col = self.vel_attr.headers["velocity"]

        for index, row in self.df_base.iterrows():
            # unweighting phase start
            if ind_unwght_start < 0 and row[force_col] < self.system_weight[0] - 5 * self.system_weight[1]:
                ind_unwght_start = index - 30  # minus 30 ms suggested by paper

            # braking phase start when force equals to force in silent phase (weight
            # of athlete)
            if ind_unwght_start > 0 and ind_brk_start < 0:  # in unweighting phase (set ind) and ind_brk not set
                if row[force_col] >= self.system_weight[0]:
                    ind_brk_start = index
                ind_unwght_end = ind_brk_start - 1

            if ind_brk_start > 0 and ind_prop_start < 0:
                if row[vel_col] >= 0.01:
                    ind_prop_start = index
                ind_brk_end = ind_prop_start - 1

            if ind_prop_start > 0 and ind_prop_end < 0:
                if row[force_col] < 10:
                    ind_prop_end = index

        return {"unweighting": (ind_unwght_start, ind_unwght_end),
                "braking": (ind_brk_start, ind_brk_end),
                "propulsive": (ind_prop_start, ind_prop_end)}

    def get_cmj_stats(self):
        idxs = self.get_phases_idx()
        ind_unwght_start = idxs["unweighting"][0]
        ind_unwght_end = idxs["unweighting"][1]
        ind_brk_start = idxs["braking"][0]
        ind_brk_end = idxs["braking"][1]
        ind_prop_start = idxs["propulsive"][0]
        ind_prop_end = idxs["propulsive"][1]
        vel_col = self.vel_attr.headers["velocity"]

        df_unwght = self.calculate_acceleration(self.df_base.iloc[ind_unwght_start: ind_unwght_end], 0.001, vel_col)
        df_brk = self.calculate_acceleration(self.df_base.iloc[ind_brk_start: ind_brk_end], 0.001, vel_col)
        df_prop = self.calculate_acceleration(self.df_base.iloc[ind_prop_start: ind_prop_end], 0.001, vel_col)
        df_neg_vel = self.calculate_acceleration(self.df_base.iloc[ind_unwght_start: ind_brk_end], 0.001, vel_col)
        df_pos_a = self.calculate_acceleration(self.df_base.iloc[ind_brk_start: ind_prop_end], 0.001, vel_col)

        """
        print(ind_unwght_start)
        print(ind_brk_start)
        print(ind_prop_start)
        print(ind_prop_end)
        print("\n")
        """
        v_peak_prop_idx = df_prop["Velocity (M/s)"].idxmax()

        stats = {'v_peak_prop': df_prop["Velocity (M/s)"].max(),
                 'v_peak_neg': df_neg_vel["Velocity (M/s)"].min(),
                 'v_avg_neg': df_neg_vel["Velocity (M/s)"].mean(),
                 't_to_v_peak_prop': df_prop.loc[v_peak_prop_idx, "Time (s)"] - df_prop.loc[ind_prop_start, "Time (s)"],
                 'v_avg_100_prop': df_prop.loc[ind_prop_start: ind_prop_start + 100, "Velocity (M/s)"].mean(),
                 'a_avg_100_prop': df_prop.loc[ind_prop_start: ind_prop_start + 100, "Acceleration (m/s^2)"].mean(),
                 'a_peak_100_prop': df_prop.loc[ind_prop_start: ind_prop_start + 100, "Acceleration (m/s^2)"].max(),
                 'v_peak_100_prop': df_prop.loc[ind_prop_start: ind_prop_start + 100, "Velocity (M/s)"].max(),
                 'a_peak_pos': df_pos_a["Acceleration (m/s^2)"].max()
                 }
        return stats

        for key, item in stats.items():
            print("{}: {:.4f}".format(key, item))

        """
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

        print("Time to v peak pos:                     {:.4f} s".format(t_to_v_peak_prop))
        print("v peak pos:                             {:.4f} m/s".format(v_peak_prop))
        print("v peak neg:                             {:.4f} m/s".format(v_peak_neg))
        print("v avg 100ms pos:                        {:.4f} m/s".format(v_avg_100_prop))
        print("a avg 100ms prop:                       {:.4f} m/s^2".format(a_avg_100_prop))
        print("a peak 100ms prop:                      {:.4f} m/s^2".format(a_peak_100_prop))
        print("v peak 100ms prop:                      {:.4f} m/s^2".format(v_peak_100_prop))
        """
        """
        print("v peak neg /  Time to v peak pos:       {:.4f}".format(v_peak_neg / t_to_v_peak_prop))
        print("v peak neg / V peak prop:               {:.4f}".format(v_peak_neg / v_peak_prop))
        print("v avg neg / V peak prop:                {:.4f}".format(v_avg_neg / v_peak_prop))
        print("v avg neg / first 100 ms v pos avg:     {:.4f} ".format(v_avg_neg / v_avg_100_prop))
        print("v peak neg / first 100 ms v pos avg:    {:.4f}".format(v_peak_neg / v_avg_100_prop))
        print("v avg neg / first 100 ms acc prop avg:  {:.4f}".format(v_avg_neg / a_avg_100_prop))
        print("v peak neg / first 100 ms acc prop avg: {:.4f}".format(v_peak_neg / a_avg_100_prop))
        """


if __name__ == "__main__":
    path = r"D:\DevProjects\PythonProjects\CMJ-statistics\data"
    with open(rf"{path}\velocity\Adam_Lewandowski-10_14_2020.csv") as csv_file:
        cmj_vel_attr = VelocityCMJAttribute(csv_file)
    with open(rf"{path}\force\Adam_Lewandowski-10_14_2020.csv") as csv_file:
        cmj_force_attr = ForceCMJAttribute(csv_file)
    cmj = CMJForceVelStats(cmj_vel_attr, cmj_force_attr, "Time (s)")
    print("Adam: ")
    stats = cmj.get_cmj_stats()
    print(stats)

    cmj_vel_attr = CMJAttribute(rf"{path}\robin\velocity.csv",
                                {"time": "Time (s)", "velocity": "Velocity (M/s)"})
    cmj_force_attr = CMJAttribute(rf"{path}\robin\force.csv",
                                  {"time": "Time (s)", "left": "Left (N)", "right": "Right (N)",
                                   "combined": "Combined (N)"})
    cmj = CMJForceVelStats(cmj_vel_attr, cmj_force_attr, "Time (s)")
    print("Robin: ")
    cmj.get_cmj_stats()

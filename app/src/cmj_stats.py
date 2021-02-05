import pandas as pd
from csv import reader
from functools import partial, reduce


class CMJAttribute:
    """
    Objects of that class contain details of particular
    attribute/characteristic of counter movement, for
    example it would be velocity or force
    """
    def __init__(self, csv_path: str, headers: dict):
        """
        :param csv_path: path to csv file
        :param headers: dictionary with key as attribute (time, velocity, left, combined etc.) and col name as value
        """
        self.csv_path = csv_path
        self.headers = headers
        self._verify_csv_header()

    def _verify_csv_header(self):
        """
        Verifies if csv file header contain
        all the columns from the arg columns list
        csv_file: path to file
        columns: list of columns names that needs to be present in csv file header
        """
        with open(self.csv_path, mode="rt") as csv_file:
            f_reader = reader(csv_file)
            headers_csv = list(next(f_reader))
            for col in list(self.headers.values()):
                if col not in headers_csv:
                    raise ValueError("Wrong csv headers. No {} column.".format(col))

    def get_df(self):
        """
        Generates dataframe from csv file provided as attribute of object
        :return: pandas dataframe with data from csv file
        """
        df = pd.read_csv(self.csv_path)
        df = df[df.columns.intersection(list(self.headers.values()))]
        return df


class VelocityCMJAttribute(CMJAttribute):
    """
    Velocity characteristic of counter movement jump.
    Inherits from CMJAttribute
    """
    def __init__(self, csv_path, headers):
        super().__init__(csv_path, headers)
        self.df_vel = super().get_df()
        self.df_pos_vel = self._get_pos_vel_df()

    def _get_pos_vel_df(self):
        """
        Finds positive velocity dataframe from base dataframe provided to object
        :return: pandas dataframe with data from positive velocity
        """
        pos_vel_idx = -1
        neg_vel_idx = -1
        for index, row in self.df_vel.iterrows():
            # setting index to 0 and then identifying positive velocity to avoid
            # negative velocity which is effect of noise
            if pos_vel_idx == -1 and row[self.headers['velocity']] < 0:
                pos_vel_idx = 0
            if pos_vel_idx == 0 and row[self.headers['velocity']] > 0:
                pos_vel_idx = index
                neg_vel_idx = 0
            # find first negative velocity index after positive velocity
            if neg_vel_idx == 0 and row[self.headers['velocity']] < 0:
                neg_vel_idx = index
                break
        df_pos_vel = self.df_vel.iloc[pos_vel_idx: neg_vel_idx]
        df_pos_vel.reset_index(drop=True)
        return df_pos_vel

    def get_pos_vel_stamp(self, stamp):
        """

        :param stamp: timestamp for which dataframe is to be created
        :return: pandas dataframe from first positive velocity index until timestamp provided in arg
        """
        return self.df_pos_vel.iloc[:stamp]

    @staticmethod
    def create_pos_vel_excel(df_pos_val, stamp, path):
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
        self.df_base = pd.merge(vel_attr.get_df(), force_attr.get_df(), how="inner", on=join_on)
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
    cmj_vel_attr = CMJAttribute(rf"{path}\adam\velocity.csv",
                                {"time": "Time (s)", "velocity": "Velocity (M/s)"})
    cmj_force_attr = CMJAttribute(rf"{path}\adam\force.csv",
                            {"time": "Time (s)", "left": "Left (N)", "right": "Right (N)", "combined": "Combined (N)"})
    cmj = CMJForceVelStats(cmj_vel_attr, cmj_force_attr, "Time (s)")
    print("Adam: ")
    cmj.get_cmj_stats()
    print("\n\n")

    cmj_vel_attr = CMJAttribute(rf"{path}\robin\velocity.csv",
                                {"time": "Time (s)", "velocity": "Velocity (M/s)"})
    cmj_force_attr = CMJAttribute(rf"{path}\robin\force.csv",
                                  {"time": "Time (s)", "left": "Left (N)", "right": "Right (N)",
                                   "combined": "Combined (N)"})
    cmj = CMJForceVelStats(cmj_vel_attr, cmj_force_attr, "Time (s)")
    print("Robin: ")
    cmj.get_cmj_stats()



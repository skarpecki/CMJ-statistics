import pandas as pd


class csv_cmj_parser:
    def __init__(self, source_path, dest_path):
        self.source_path = source_path
        self.dest_path = dest_path
        self.g = 9.80665

    def get_stats_for_timestamp(self, stamp: int):
        df = pd.read_csv(self.source_path + r"\velocity.csv")

        negative_velocity_flag = False
        postive_velocity_index = 0
        for index, row in df.iterrows():
            if row['Velocity (M/s)'] < 0:
                negative_velocity_flag = True
            if negative_velocity_flag and row['Velocity (M/s)'] > 0:
                positive_velocity_index = index
                break
        positive_val = df.iloc[positive_velocity_index: positive_velocity_index + stamp]
        positive_val.reset_index(drop=True)
        for index, row in positive_val.iterrows():
            positive_val.loc[index, "Acceleration (M/s^2)"] = (df.loc[index, "Velocity (M/s)"] - df.loc[
                index - 1, "Velocity (M/s)"]) / (df.loc[index, "Time (s)"] - df.loc[index - 1, "Time (s)"])

        stats = positive_val.describe()[["Velocity (M/s)", "Acceleration (M/s^2)"]]
        stats = stats.loc[['mean', 'min', 'max']]

        writer = pd.ExcelWriter(f"{self.dest_path}\\{stamp}.xlsx", engine='xlsxwriter')
        positive_val.to_excel(writer, sheet_name=f"{stamp}_data")
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

    def get_stats(self):
        df_velocity = pd.read_csv(self.source_path + r"\velocity.csv")
        df_force = pd.read_csv(self.source_path + r"\force.csv")
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
                    for i in range(5):
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
                if row["Acceleration (m/s^2)"] < (-1 * g + 0.1):
                    ind_prop_end = index
                    for i in range(5):
                        if row["Acceleration (m/s^2)"] > (-1 * g + 0.2):
                            ind_prop_end = -1

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
        a_peak_pos = df_pos_a["Acceleration (m/s^2)"].max()

        print("Time to v peak pos:                      {:.4f} s".format(t_to_v_peak_prop))
        print("v peak pos:                              {:.4f} m/s".format(v_peak_prop))
        print("v peak neg:                             {:.4f} m/s".format(v_peak_neg))
        print("v avg 100ms pos:                        {:.4f} m/s".format(v_avg_100_prop))
        print("a avg 100ms prop:                       {:.4f} m/s^2".format(a_avg_100_prop))
        print("v peak neg /  Time to v peak pos:        {:.4f}".format(v_peak_neg / t_to_v_peak_prop))
        print("v peak neg / V peak prop:               {:.4f}".format(v_peak_neg / v_peak_prop))
        print("v avg neg / V peak prop:                {:.4f}".format(v_avg_neg / v_peak_prop))
        print("v avg neg / first 100 ms v pos avg:     {:.4f} ".format(v_avg_neg / v_avg_100_prop))
        print("v peak neg / first 100 ms v pos avg:    {:.4f}".format(v_peak_neg / v_avg_100_prop))
        print("v avg neg / first 100 ms acc prop avg:  {:.4f}".format(v_avg_neg / a_avg_100_prop))
        print("v peak neg / first 100 ms acc prop avg: {:.4f}".format(v_peak_neg / a_avg_100_prop))


if __name__ == "__main__":
    parser = csv_cmj_parser("data.csv", "sample")
    stamps = [50, 100, 150, 200]
    for stamp in stamps:
        parser.get_stats_for_timestamp(stamp)

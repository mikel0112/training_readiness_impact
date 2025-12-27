import datetime
import json
import requests
import pandas as pd
import numpy as np
import os
from redmail import gmail
import matplotlib.pyplot as plt
import os
from pathlib import Path
from fpdf import FPDF


class Intervals:
    """ """

    BASE_URL = "https://intervals.icu"

    def __init__(self, athlete_id, api_key, session=None):
        """ """
        self.athlete_id = athlete_id
        self.password = api_key
        self.session = session

    def _get_session(self):
        if self.session is not None:
            return self.session

        self.session = requests.Session()

        self.session.auth = ("API_KEY", self.password)
        return self.session

    def _make_request(self, method, url, params=None):
        session = self._get_session()

        res = session.request(method, url, params=params)

        if res.status_code != 200:
            raise Exception("Error on request:" + str(res))

        return res

    def activities(self, start_date, end_date=None):
        """
        Returns all your activities formatted in CSV

        :return: Text data in CSV format
        :rtype: str
        """
        if type(start_date) is not datetime.date:
            raise TypeError("dateperrequired")

        params = {}

        if end_date is not None:
            if type(end_date) is not datetime.date:
                raise TypeError("dateperrequired")
            end_date = end_date + datetime.timedelta(days=1)
            params["oldest"] = start_date.isoformat()
            params["newest"] = end_date.isoformat()
            url = "{}/api/v1/athlete/{}/activities".format(
                Intervals.BASE_URL, self.athlete_id
            )
        else:
            url = "{}/api/v1/athlete/{}/activities/{}".format(
                Intervals.BASE_URL, self.athlete_id, start_date.isoformat()
            )
        res = self._make_request("get", url, params)
        j = res.json()
        if type(j) is list:
            result = []
            for item in j:
                result.append(item)
            return result

        return j

    def activities_csv(self):
        """
        Returns all your activities formatted in CSV

        :return: Text data in CSV format
        :rtype: str
        """
        url = "{}/api/v1/athlete/{}/activities.csv".format(
            Intervals.BASE_URL, self.athlete_id
        )
        res = self._make_request("get", url)
        return res.text

    def activity(self, activity_id):
        """ """
        url = "{}/api/v1/activity/{}".format(Intervals.BASE_URL, activity_id)
        res = self._make_request("get", url)
        return res.json()
        # return Activity(**res.json())

    def athlete(self, athlete_id):
        """ """
        url = "{}/api/v1/athlete/{}".format(Intervals.BASE_URL, athlete_id)
        res = self._make_request("get", url)
        fields = res.json()
        ride = run = swim = other = {}
        for sport in fields["sportSettings"]:
            if "Ride" in sport["types"]:
                ride = sport
                print("Ride", type(sport))
            if "Run" in sport["types"]:
                run = sport
                print("Run")
            if "Swim" in sport["types"]:
                swim = sport
                print("Swim")
            if "Other" in sport["types"]:
                other = sport
                print("Other")
        return ride, run, swim, other

    def activitiy_streams(self, activity_id):
        """
        Returns all your activities formatted in CSV

        :return: Text data in CSV format
        :rtype: str
        """
        url = "{}/api/v1/activity/{}/streams".format(Intervals.BASE_URL, activity_id)
        res = self._make_request("get", url)
        j = res.json()
        per= []
        watts = []
        cadence = []
        heartrate = []
        distance = []
        altitude = []
        latlng = []
        velocity_smooth = []
        temp = []
        torque = []
        respiration = []
        for stream in j:
            try:
                if stream["type"] == "time":
                    per= stream
                elif stream["type"] == "watts":
                    watts = stream
                elif stream["type"] == "cadence":
                    cadence = stream
                elif stream["type"] == "heartrate":
                    heartrate = stream
                elif stream["type"] == "distance":
                    distance = stream
                elif stream["type"] == "altitude":
                    altitude = stream
                elif stream["type"] == "latlng":
                    latlng = stream
                elif stream["type"] == "velocity_smooth":
                    velocity_smooth = stream
                elif stream["type"] == "temp":
                    temp = stream
                elif stream["type"] == "torque":
                    torque = stream
                elif stream["type"] == "respiration":
                    respiration = stream
            except Exception as e:
                print("Error on activity", activity_id, ":", e)

        return (
            per,
            watts,
            cadence,
            heartrate,
            distance,
            altitude,
            latlng,
            velocity_smooth,
            temp,
            torque,
            respiration,
        )

    def wellness(self, start_date, end_date=None):
        """ """
        if type(start_date) is not datetime.date:
            raise TypeError("dateperrequired")

        params = {}

        if end_date is not None:
            if type(end_date) is not datetime.date:
                raise TypeError("dateperrequired")

            params["oldest"] = start_date.isoformat()
            params["newest"] = end_date.isoformat()
            url = "{}/api/v1/athlete/{}/wellness".format(
                Intervals.BASE_URL, self.athlete_id
            )
        else:
            url = "{}/api/v1/athlete/{}/wellness/{}".format(
                Intervals.BASE_URL, self.athlete_id, start_date.isoformat()
            )

        res = self._make_request("get", url, params)
        j = res.json()
        if type(j) is list:
            result = []
            for item in j:
                result.append(item)
            return result
        return j

    def workouts(self):
        """ """
        url = "{}/api/v1/athlete/{}/workouts".format(
            Intervals.BASE_URL, self.athlete_id
        )

        res = self._make_request("get", url)
        j = res.json()
        if type(j) is list:
            result = []
            for item in j:
                result.append(item)
            return result

        raise TypeError("Unexpected result from server")

    def workout(self, workout_id):
        """ """
        url = "{}/api/v1/athlete/{}/workouts/{}".format(
            Intervals.BASE_URL, self.athlete_id, workout_id
        )

        res = self._make_request("get", url)
        return res.json()

    def power_curve(
        self,
        newest=datetime.datetime.now(),
        curves="90d",
        type="Ride",
        include_ranks=False,
        sub_max_efforts=0,
        filters='[{"field_id": "type", "value": ["Ride", "VirtualRide"]}]',
    ):
        """ """
        url = f"{self.BASE_URL}/api/v1/athlete/{self.athlete_id}/power-curves"
        params = {
            "curves": curves,
            "type": type,
            "includeRanks": include_ranks,
            "subMaxEfforts": f"{sub_max_efforts}",
            "filters": filters,
            "newest": newest.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        res = self._make_request("get", url, params=params)
        return res.json()
    
    def summary_stats(self, start_date=None, end_date=None):
        url = f"{self.BASE_URL}/api/v1/athlete/{self.athlete_id}/athlete-summary"
        params = {}
        params["start"] = start_date.isoformat()
        params["end"] = end_date.isoformat()
        #params['tags'] = 'Coaching'
        res = self._make_request("get", url, params=params)
        return res.json()



class SaveData:
    def __init__(self, athlete_name):
        self.athlete_name = athlete_name

    def wellness_data(self, wellness_data, old_df):
        wellness_df = pd.DataFrame(wellness_data)
        interesting_columns = [
            "id",
            "rampRate",
            "weight",
            "restingHR",
            "hrv",
            "sleepSecs",
            "stress",
            "motivation",
            "injury",
        ]
        clean_df = wellness_df[interesting_columns]
        # change column name from id to date
        clean_df = clean_df.rename(columns={"id": "date"})
        # sleep values from seconds to hours
        clean_df["sleepSecs"] = clean_df["sleepSecs"] / 3600
        # merge data from both dfs
        wellness_clean_df = pd.concat([old_df, clean_df], ignore_index=True)
        os.makedirs(f"data/{self.athlete_name}", exist_ok=True)
        wellness_clean_df.to_csv(f"data/{self.athlete_name}/wellness.csv")

    def activities_data(self, activities_data, old_act_df):
        df_activities = pd.DataFrame(activities_dict)
        activities_clean_df = df_activities[[
            'id',
            'start_date_local', 
            'type',
            'moving_time',
            'total_elevation_gain',
            'distance',
            'average_speed',
            'max_heartrate',
            'average_heartrate',
            'average_cadence',
            'icu_average_watts',
            'icu_rpe', 
            'feel',
            'icu_efficiency_factor',

        ]]
        # change date format to datetime.date
        activities_clean_df['start_date_local'] = pd.to_datetime(activities_clean_df['start_date_local']).dt.date
        # create session quality column
        activities_clean_df['session_quality'] = activities_clean_df['feel'] * activities_clean_df['icu_efficiency_factor']
        # change units to average speed
        activities_clean_df.loc[activities_clean_df['type'] == 'Ride', 
                                'average_speed'] = activities_clean_df['average_speed'] * 3.6
        activities_clean_df.loc[activities_clean_df['type'] == 'Run',
                                'average_speed'] = 1/(activities_clean_df['average_speed'] * 0.06)
        activities_clean_df.loc[activities_clean_df['type'] == 'TrailRun',
                                'average_speed'] = 1/(activities_clean_df['average_speed'] * 0.06)
        activities_clean_df['moving_time'] = activities_clean_df['moving_time'] / 3600
        activities_clean_df['distance'] = activities_clean_df['distance'] / 1000
        # merge data from both dfs
        activities_clean_df = pd.concat([old_act_df, activities_clean_df], ignore_index=True)
        os.makedirs(f"data/{self.athlete_name}", exist_ok=True)
        activities_clean_df.to_csv(f"data/{self.athlete_name}/activities.csv")
    
    def weekly_stats_data(self, weekly_stats_data, athlete, old_weekly_stats_df):
        df_weekly_stats = pd.DataFrame(weekly_stats_data)
        # save the rows that in a certain column contain athlete name
        df_weekly_stats = df_weekly_stats[df_weekly_stats['athlete_name'] == athlete]
        clean_df = df_weekly_stats[[
            'count',
            'time',
            'calories',
            'total_elevation_gain',
            'training_load',
            'distance',
            'date',
            'form',
            'rampRate',
            'weight',
            'timeInZones',
            'byCategory'
        ]]
        expanded_columns = pd.DataFrame(clean_df['timeInZones'].tolist(), index=clean_df.index)
        expanded_columns.columns = [f"Z_{i}" for i in range(1, len(expanded_columns.columns) + 1)]
        expanded_columns['total'] = expanded_columns.sum(axis=1)
        total_col = expanded_columns.iloc[:, -1]
        expanded_columns_percentage = expanded_columns.div(total_col, axis=0)
        expanded_columns_percentage = expanded_columns_percentage.mul(100)
        expanded_columns_percentage = expanded_columns_percentage.drop(columns=['total'])
        clean_df = pd.concat([clean_df, expanded_columns_percentage], axis=1)

        expanded_columns = pd.DataFrame(clean_df['byCategory'].tolist(), index=clean_df.index)
        rows, cols = expanded_columns.shape
        types_df = pd.DataFrame(columns=[
            'run_time',
            'run_count',
            'run_elevation_gain',
            'run_distance',
            'ride_time',
            'ride_count',
            'ride_elevation_gain',
            'ride_distance',
            'strength_time',
            'strength_count',
            'strength_elevation_gain',
            'strength_distance'
        ])
        for i in range(rows):
            for j in range(cols):
                type_dict = expanded_columns.iloc[i, j]
                if type_dict['category'] == 'Run':
                    types_df.loc[i, 'run_time'] = type_dict['time']
                    types_df.loc[i, 'run_count'] = type_dict['count']
                    types_df.loc[i, 'run_elevation_gain'] = type_dict['total_elevation_gain']
                    types_df.loc[i, 'run_distance'] = type_dict['distance']
                elif type_dict['category'] == 'Ride':
                    types_df.loc[i, 'ride_time'] = type_dict['time']
                    types_df.loc[i, 'ride_count'] = type_dict['count']
                    types_df.loc[i, 'ride_elevation_gain'] = type_dict['total_elevation_gain']
                    types_df.loc[i, 'ride_distance'] = type_dict['distance']
                elif type_dict['category'] == 'Workout':
                        types_df.loc[i, 'strength_time'] = type_dict['time']
                        types_df.loc[i, 'strength_count'] = type_dict['count']
                        types_df.loc[i, 'strength_elevation_gain'] = type_dict['total_elevation_gain']
                        types_df.loc[i, 'strength_distance'] = type_dict['distance']
        
        index_list = clean_df.index.tolist()
        types_df.index = index_list
        clean_df = pd.concat([clean_df, types_df], axis=1)

        # drop unnecessary columns
        clean_df = clean_df.drop(columns=['timeInZones', 'byCategory'])

        # change columns units
        clean_df['time'] = clean_df['time'] / 3600
        clean_df['distance'] = clean_df['distance'] / 1000
        clean_df['run_time'] = clean_df['run_time'] / 3600
        clean_df['run_distance'] = clean_df['run_distance'] / 1000
        clean_df['ride_time'] = clean_df['ride_time'] / 3600
        clean_df['ride_distance'] = clean_df['ride_distance'] / 1000
        clean_df['strength_time'] = clean_df['strength_time'] / 3600
        clean_df['strength_distance'] = clean_df['strength_distance'] / 1000


        # merge data from both dfs
        df_weekly_stats = pd.concat([old_weekly_stats_df, clean_df], ignore_index=True)
        os.makedirs(f"data/{athlete}", exist_ok=True)
        df_weekly_stats.to_csv(f"data/{athlete}/weekly_stats.csv")

if __name__ == "__main__":

    # get credentials
    credentials_info = json.load(open("docs/p_info.json"))
    for user, data in credentials_info.items():
        if data['role'] == "coach":
            coach_name = user
    coach_id = credentials_info[coach_name]["id"]
    api_key = credentials_info[coach_name]["password"]

    intervals = Intervals(coach_id, api_key)
    save_data = SaveData(coach_name)

    ########-------------------------------------########
    ########      DOWNLOAD WELLNESS DATA         ########
    ########-------------------------------------########

    # find dates
    if os.path.exists(f"data/{coach_name}/wellness.csv"):
        old_wellness_df = pd.read_csv(f"data/{coach_name}/wellness.csv")
        start_date = old_wellness_df['date'].max()
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        # add one day to start date
        start_date = start_date + datetime.timedelta(days=1)
    else:
        start_date = datetime.datetime.strptime(input("Start date (YYYY-MM-DD): "), "%Y-%m-%d")
        old_wellness_df = pd.DataFrame()
    end_date = datetime.date.today()

    # download
    if start_date.date() < end_date:
        wellness_df = intervals.wellness(start_date.date(), end_date)

        # save data
        save_data.wellness_data(wellness_df, old_wellness_df)

    #---------------------------------------------------#
    #---------------------------------------------------#


    ########-------------------------------------########
    ########      DOWNLOAD ACTIVITIES DATA       ########
    ########-------------------------------------########
    # download activities csv
    if os.path.exists(f"data/{coach_name}/activities.csv"):
        old_act_df = pd.read_csv(f"data/{coach_name}/activities.csv")
    else:
        start_date = datetime.datetime.strptime(input("Start date (YYYY-MM-DD): "), "%Y-%m-%d")
        old_act_df = pd.DataFrame()

    if start_date.date() < end_date:
        activities_dict = intervals.activities(start_date.date(), end_date)
    
        # save data
        save_data.activities_data(activities_dict, old_act_df)

    #---------------------------------------------------#
    #---------------------------------------------------#


    ########-------------------------------------########
    ########      DOWNLOAD WEEKLY STATS DATA     ########
    ########-------------------------------------########
    # download activities csv
    today_date = datetime.date.today()
    # the sunday of the week before this week
    end_date = today_date - datetime.timedelta(days=today_date.weekday()) - datetime.timedelta(days=1)
    if os.path.exists(f"data/{coach_name}/weekly_stats.csv"):
        old_weekly_stats_df = pd.read_csv(f"data/{coach_name}/weekly_stats.csv")
    else:
        start_date = datetime.datetime.strptime(input("Start date (YYYY-MM-DD): "), "%Y-%m-%d")
        old_weekly_stats_df = pd.DataFrame()
    
    if start_date.date() < end_date:
        weekly_stats_data = intervals.summary_stats(start_date.date(), end_date)
        # list of athletes
        athletes = []
        for athlete, data in credentials_info.items():
            athletes.append(data['icu_name'])
            # save data for every athlete
        for athlete in athletes:
            save_data.weekly_stats_data(weekly_stats_data, athlete, old_weekly_stats_df)


    #---------------------------------------------------#
    #---------------------------------------------------#
    
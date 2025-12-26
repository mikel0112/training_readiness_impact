import datetime
import json
import requests
import pandas as pd
import numpy as np
import os
from redmail import gmail


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
            raise TypeError("datetime required")

        params = {}

        if end_date is not None:
            if type(end_date) is not datetime.date:
                raise TypeError("datetime required")
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
        time = []
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
                    time = stream
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
            time,
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
            raise TypeError("datetime required")

        params = {}

        if end_date is not None:
            if type(end_date) is not datetime.date:
                raise TypeError("datetime required")

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

class WriteEmail():
    def __init__(self, athlete_name, start_week_date, fin_week_date, total_hours, total_distance, total_elevation_gain, form, ramp):
        self.athlete_name = athlete_name
        self.start_week_date = start_week_date
        self.fin_week_date = fin_week_date
        self.total_hours = total_hours
        self.total_distance = total_distance
        self.form = form
        self.ramp = ramp
        self.total_elevation_gain = total_elevation_gain

    def send_email(self, info, athlete_name):

        gmail.user_name = info[athlete_name]["email"]
        gmail.password = info[athlete_name]["email_pass"]
        gmail.send(
            subject="Estadísticas semanales de " + athlete_name,
            receivers=[gmail.user_name],
            html=open("src/email_template.html", "r").read(),
            body_params={
                "athlete_name": athlete_name,
                "comentario_final" : ""
            },
            images={
                "grafico_1": "src/grafico_1.png",
                "grafico_2": "src/grafico_2.png",
                "grafico_3": "src/grafico_3.png"
            }
        )

if __name__ == "__main__":

    # get athlete credentials
    athlete_name = input("Athlete name: ")
    api_info = json.load(open("docs/p_info.json"))
    athlete_id = api_info[athlete_name]["id"]
    api_key = api_info[athlete_name]["password"]

    intervals = Intervals(athlete_id, api_key)

    # download athletes summary stats
    summary_stats = intervals.summary_stats(datetime.date(2025,12,15), datetime.date(2025,12,21))
    for week in summary_stats:
        if week['athlete_name'] == "Jon1998":
            start_week_date = week['date']
            # convert to datetime
            start_week_date = datetime.datetime.strptime(start_week_date, '%Y-%m-%d')
            fin_week_date = start_week_date + datetime.timedelta(days=7)
            # back to string dates
            start_week_date = start_week_date.strftime('%Y-%m-%d')
            fin_week_date = fin_week_date.strftime('%Y-%m-%d')
            total_hours = round(week['time']/3600,2)
            total_distance = round(week['distance']/1000,2)
            total_elevation_gain = week['total_elevation_gain']
            form = week['form']
            ramp = week['rampRate']
            for activity in week['byCategory']:
                if activity['category'] == 'Run':
                    run_hours = round(activity['time']/3600,2) 
                    run_distance = round(activity['distance']/1000,2)
                    run_elevation_gain = activity['total_elevation_gain']
                elif activity['category'] == 'Ride':
                    ride_hours = round(activity['time']/3600,2) 
                    ride_distance = round(activity['distance']/1000,2)
                    ride_elevation_gain = activity['total_elevation_gain']
                else:
                    other_hours = round(activity['time']/3600,2) 
                    other_distance = round(activity['distance']/1000,2)
                    other_elevation_gain = activity['total_elevation_gain']
    
    # send weekly stats by email
    info = json.load(open("docs/p_info.json"))
    write_email = WriteEmail(athlete_name, start_week_date, fin_week_date, total_hours, total_distance, total_elevation_gain, form, ramp)
    write_email.send_email(info, athlete_name)

    # download wellness data
    if os.path.exists(f"data/unified_data_{athlete_name}.csv"):
        old_df = pd.read_csv(f"data/unified_data_{athlete_name}.csv")
        start_date = old_df['date'].max()
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        # add one day to start date
        start_date = start_date + datetime.timedelta(days=1)
    else:
        start_date = datetime.datetime.strptime(input("Start date (YYYY-MM-DD): "), "%Y-%m-%d")
    end_date = datetime.date.today()
    wellness_data = intervals.wellness(start_date.date(), end_date)
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
    wellness_clean_df = wellness_df[interesting_columns]

    # download activities csv
    activities_dict = intervals.activities(start_date.date(), end_date)
    df_activities = pd.DataFrame(activities_dict)
    activities_clean_df = df_activities[['id','start_date_local', 'type','icu_rpe', 'feel','icu_efficiency_factor']]
    #eliminate activities that are not run or trailrun
    activities_clean_df = activities_clean_df[
        (activities_clean_df['type'] == 'Run') | (activities_clean_df['type'] == 'TrailRun')
    ]
    # change date format to datetime.date
    activities_clean_df['start_date_local'] = pd.to_datetime(activities_clean_df['start_date_local']).dt.date
    # create session quality column
    activities_clean_df['session_quality'] = activities_clean_df['feel'] * activities_clean_df['icu_efficiency_factor']
    # get activities id list
    activity_ids = activities_clean_df['id'].tolist()

    # download activity streams for each activity
    for activity_id in activity_ids:
        (
            time,
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
        ) = intervals.activitiy_streams(activity_id)
        # 2min to 5 min power and heartrate avegrage

        start_power = round(float(np.mean(watts['data'][120:300])),2)
        start_heartrate = round(float(np.mean(heartrate['data'][120:300])),2)

        # last 3 min power and heartrate
        end_power = round(float(np.mean(watts['data'][-180:])),2)
        end_heartrate = round(float(np.mean(heartrate['data'][-180:])),2)
        
        # add data to activities_clean_df
        activities_clean_df.loc[activities_clean_df['id'] == activity_id, 'start_power'] = start_power
        activities_clean_df.loc[activities_clean_df['id'] == activity_id, 'start_heartrate'] = start_heartrate
        activities_clean_df.loc[activities_clean_df['id'] == activity_id, 'end_power'] = end_power
        activities_clean_df.loc[activities_clean_df['id'] == activity_id, 'end_heartrate'] = end_heartrate
        
    # convert to datetime.date
    wellness_clean_df['id'] = pd.to_datetime(wellness_clean_df['id']).dt.date
    activities_clean_df['start_date_local'] = pd.to_datetime(activities_clean_df['start_date_local']).dt.date
    # UNIFY BOTH DATAFRAMES using id and date
    unified_df = pd.merge(
        activities_clean_df,
        wellness_clean_df,
        left_on=['start_date_local'],
        right_on=[ 'id'],
        how='inner'
    )
    # if row contains nan eliminate it
    unified_df = unified_df.dropna()

    # drop type column
    unified_df = unified_df.drop(columns=['type'])
    # drop id_x column
    unified_df = unified_df.drop(columns=['id_x'])
    # drop id_y column
    unified_df = unified_df.drop(columns=['id_y'])
    # put start_date local as date index
    unified_df = unified_df.set_index('start_date_local')
    # order by start_date_local
    unified_df = unified_df.sort_index(ascending=True)
    # change index name to date
    unified_df.index.name = 'date'

    # update df
    if os.path.exists(f"data/unified_data_{athlete_name}.csv"):
        combined_df = pd.concat([old_df, unified_df])
        combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
        unified_df = combined_df.sort_index(ascending=True)
    # save to csv
    unified_df.to_csv(f"data/unified_data_{athlete_name}.csv", index=True)

    
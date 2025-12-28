import datetime
import json
import requests
import pandas as pd
import numpy as np
import os
from redmail import gmail
import matplotlib.pyplot as plt
from pathlib import Path
from fpdf import FPDF
from google.cloud import storage
from io import StringIO
import logging

logger = logging.getLogger(__name__)

# Configuración de Cloud Storage
BUCKET_NAME = "weeklytrainingemail-data"
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

def read_csv_from_gcs(blob_path):
    """Lee un CSV desde Cloud Storage"""
    try:
        blob = bucket.blob(blob_path)
        if blob.exists():
            content = blob.download_as_string()
            return pd.read_csv(StringIO(content.decode('utf-8')))
        else:
            logger.info(f"Archivo {blob_path} no existe en GCS")
            return None
    except Exception as e:
        logger.error(f"Error al leer {blob_path} desde GCS: {e}")
        return None

def save_csv_to_gcs(df, blob_path):
    """Guarda un DataFrame como CSV en Cloud Storage"""
    try:
        blob = bucket.blob(blob_path)
        csv_string = df.to_csv(index=False)
        blob.upload_from_string(csv_string, content_type='text/csv')
        logger.info(f"✓ CSV guardado en GCS: {blob_path}")
    except Exception as e:
        logger.error(f"Error al guardar {blob_path} en GCS: {e}")
        raise


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
        clean_df = clean_df.rename(columns={"id": "date"})
        clean_df["sleepSecs"] = clean_df["sleepSecs"] / 3600
        wellness_clean_df = pd.concat([old_df, clean_df], ignore_index=True)
        
        # Guardar en Cloud Storage en lugar de local
        save_csv_to_gcs(wellness_clean_df, f"data/{self.athlete_name}/wellness.csv")

    def activities_data(self, activities_data, old_act_df):
        df_activities = pd.DataFrame(activities_data)
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
        activities_clean_df['start_date_local'] = pd.to_datetime(activities_clean_df['start_date_local']).dt.date
        activities_clean_df['session_quality'] = activities_clean_df['feel'] * activities_clean_df['icu_efficiency_factor']
        activities_clean_df.loc[activities_clean_df['type'] == 'Ride', 
                                'average_speed'] = activities_clean_df['average_speed'] * 3.6
        activities_clean_df.loc[activities_clean_df['type'] == 'Run',
                                'average_speed'] = 1/(activities_clean_df['average_speed'] * 0.06)
        activities_clean_df.loc[activities_clean_df['type'] == 'TrailRun',
                                'average_speed'] = 1/(activities_clean_df['average_speed'] * 0.06)
        activities_clean_df['moving_time'] = activities_clean_df['moving_time'] / 3600
        activities_clean_df['distance'] = activities_clean_df['distance'] / 1000
        activities_clean_df = pd.concat([old_act_df, activities_clean_df], ignore_index=True)
        
        # Guardar en Cloud Storage en lugar de local
        save_csv_to_gcs(activities_clean_df, f"data/{self.athlete_name}/activities.csv")
    
    def weekly_stats_data(self, weekly_stats_data, athlete, old_weekly_stats_df):
        df_weekly_stats = pd.DataFrame(weekly_stats_data)
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
                if type_dict:
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

        clean_df = clean_df.drop(columns=['timeInZones', 'byCategory'])

        clean_df['time'] = clean_df['time'] / 3600
        clean_df['distance'] = clean_df['distance'] / 1000
        clean_df['run_time'] = clean_df['run_time'] / 3600
        clean_df['run_distance'] = clean_df['run_distance'] / 1000
        clean_df['ride_time'] = clean_df['ride_time'] / 3600
        clean_df['ride_distance'] = clean_df['ride_distance'] / 1000
        clean_df['strength_time'] = clean_df['strength_time'] / 3600
        clean_df['strength_distance'] = clean_df['strength_distance'] / 1000

        df_weekly_stats = pd.concat([old_weekly_stats_df, clean_df], ignore_index=True)
        
        # Guardar en Cloud Storage en lugar de local
        save_csv_to_gcs(df_weekly_stats, f"data/{athlete}/weekly_stats.csv")
import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class CleanData:
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
        return wellness_clean_df
    

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
        return activities_clean_df
        
    def weekly_stats_data(self, weekly_stats_data, athlete):
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

        return clean_df
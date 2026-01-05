import sys
import os
# Añade la carpeta raíz al buscador de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.googlecloud import GCMySQL, GCcredential
from utils.cleandata import CleanData
from utils.intervals import Intervals
import pandas as pd
import time
import logging
import datetime
from flask import Flask
from sqlalchemy import text




logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Esto le dice a Python que busque archivos en la carpeta actual del script
dir_actual = os.path.dirname(os.path.abspath(__file__))
if dir_actual not in sys.path:
    sys.path.append(dir_actual)


app = Flask(__name__)

def update_weekly_stats_data(pool, coach_id, api_key, coach_name, credentials_dict):
    logger.info("Comprobando si existen datos en la base de datos...")
    # list of athletes
    athletes = []
    athletes_unified = []
    for athlete, data in credentials_dict.items():
        if 'icu_name' in data:
            name_unified = data['icu_name'].replace(" ", "_")
            athletes_unified.append(name_unified)
            athletes.append(data['icu_name'])
    logger.info(f"Atletas encontrados: {athletes}")
    download_data = Intervals(coach_id, api_key)
    for athlete in athletes_unified:
        # extract latest date in any of the tables
        logger.info(f"Buscando datos para {athlete} en la base de datos...")
        query = f"SELECT date FROM weekly_stats.weekly_stats_{athlete} ORDER BY date DESC LIMIT 1"
        try:
            result = pd.read_sql_query(query, pool)
            end_date = datetime.date.today()
            weekday = end_date.weekday()
            # download weekly data just on sundays
            #if weekday == 6:
            start_date = end_date - datetime.timedelta(days=weekday) 
            # eliminar datos de la base de datos
            previous_week_data = start_date - datetime.timedelta(days=7)
            query_1 = text(f"DELETE FROM weekly_stats.weekly_stats_{athlete} WHERE date = '{start_date}'")
            query_2 = text(f"DELETE FROM weekly_stats.weekly_stats_{athlete} WHERE date = '{previous_week_data}'")
            # execute query
            with pool.begin() as conn:
                conn.execute(query_1)
                conn.execute(query_2)
            # download new data
            logger.info(f"Descargando datos desde {previous_week_data} hasta {end_date}...")
            weekly_stats_data = download_data.summary_stats(previous_week_data, end_date)
            logger.info("✓ Datos descargados")
                    
            logger.info(f"Guardando datos para {athlete}...")
            clean_data = CleanData(athletes[athletes_unified.index(athlete)])
            df_weekly_stats = clean_data.weekly_stats_data(weekly_stats_data, athletes[athletes_unified.index(athlete)])
            logger.info(f"El index es: {df_weekly_stats.index}")
            logger.info(f"El shape es: {df_weekly_stats.shape}")
            # create table
            df_weekly_stats.to_sql(f'weekly_stats_{athlete}', pool, schema='weekly_stats', if_exists='append', index=False)
            #else:
                #logger.info("No es domingo, no se descargan datos")
                #break

        except Exception as e:
            logger.info("No existen datos en la base de datos")
            logger.info(f"Error al descargar datos: {e}")
            logger.info("Descargando estadísticas semanales...")
            ########-------------------------------------########
            ########      DOWNLOAD WEEKLY STATS DATA     ########
            ########-------------------------------------########
            logger.info("Descargando estadísticas semanales...")

            end_date = datetime.date.today()
            logger.info(f"Fecha fin: {end_date}")
            
            start_date = end_date - datetime.timedelta(days=366)
            logger.info(f"Archivo nuevo. Descargando últimos 366 días desde: {start_date}")
            
            if start_date <= end_date:
                logger.info(f"Descargando datos desde {start_date} hasta {end_date}...")
                weekly_stats_data = download_data.summary_stats(start_date, end_date)
                logger.info("✓ Datos descargados")
                
                # save data for every athlete
                clean_data = CleanData(coach_name)
                for athl in athletes:
                    logger.info(f"Guardando datos para {athl}...")
                    df_weekly_stats = clean_data.weekly_stats_data(weekly_stats_data, athl)
                    df_columns = df_weekly_stats.columns.tolist()
                    # create table
                    df_weekly_stats.to_sql(f'weekly_stats_{athletes_unified[athletes.index(athl)]}', pool, schema='weekly_stats', if_exists='append', index=False)
                break
            else:
                logger.info("No hay nuevos datos para descargar")
                break

def update_weekly_stats_moving_averages(pool, coach_id, api_key, coach_name, credentials_dict):
    columns = ['Athlete varchar(255) NOT NULL PRIMARY KEY',
            'MA_form_4w float',
            'MA_form_12w float',
            'MA_form_52w float',
            'MA_time_4w float',
            'MA_time_12w float',
            'MA_time_52w float',
            'MA_elevation_4w float',
            'MA_elevation_12w float',
            'MA_elevation_52w float'
        ]
    # use columns to create query
    table_columns = ', '.join(columns)
    query_1 = text(f"CREATE TABLE IF NOT EXISTS weekly_stats_moving_averages ({table_columns})")
    query_2 = text("TRUNCATE TABLE weekly_stats_moving_averages")
    with pool.begin() as conn:
        conn.execute(query_1)
        conn.execute(query_2)
    
    athletes_unified = []
    athletes = []
    for key, data in credentials_dict.items():
        if 'icu_name' in data:
            name_unified = data['icu_name'].replace(" ", "_")
            athletes_unified.append(name_unified)
            athletes.append(data['icu_name'])
    logger.info(f"Atletas encontrados: {athletes}")

    # extract data from every athlete for the last 52 weeks
    data = []
    for athlete in athletes_unified:
        logger.info(f"Guardando datos para {athlete}...")
        query = f"SELECT * FROM weekly_stats.weekly_stats_{athlete} ORDER BY date DESC LIMIT 52"
        df_athlete = pd.read_sql(query, pool)
        logger.info(f"El shape es: {df_athlete.shape}")

        # calculate moving averages
        athlete_data = {
        'Athlete': athletes[athletes_unified.index(athlete)],
        'MA_form_4w': df_athlete['form'].iloc[0:4].mean(),
        'MA_form_12w': df_athlete['form'].iloc[0:12].mean(),
        'MA_form_52w': df_athlete['form'].mean(),
        'MA_time_4w': df_athlete['time'].iloc[0:4].mean(),
        'MA_time_12w': df_athlete['time'].iloc[0:12].mean(),
        'MA_time_52w': df_athlete['time'].mean(),
        'MA_elevation_4w': df_athlete['total_elevation_gain'].iloc[0:4].mean(),
        'MA_elevation_12w': df_athlete['total_elevation_gain'].iloc[0:12].mean(),
        'MA_elevation_52w': df_athlete['total_elevation_gain'].mean()
    }
        data.append(athlete_data)

    moving_avg_df = pd.DataFrame(data)
    # save data
    moving_avg_df.to_sql('weekly_stats_moving_averages', pool, schema='weekly_stats', if_exists='append', index=False)


def update_weellness_daily_data(pool, coach_id, api_key, coach_name, credentials_dict):
    download_data = Intervals(coach_id, api_key)
    clean_data = CleanData(coach_name)
    athletes_unified = []
    athletes = []
    keys_list = list(credentials_dict.keys())
    for key, data in credentials_dict.items():
        if 'icu_name' in data:
            name_unified = data['icu_name'].replace(" ", "_")
            athletes_unified.append(name_unified)
            athletes.append(data['icu_name'])
    logger.info(f"Atletas encontrados: {athletes}")

    # creata table
    for athlete in athletes_unified:
        logger.info(f"Guardando datos para {athlete}...")
        #if athlete == 'Mikel_Campo': # cambiar cuando ids del resto
        try:
                query = f"SELECT * FROM wellness_data.wellness_daily_{athlete}"
                df_athlete = pd.read_sql(query, pool)
                logger.info(f"El shape es: {df_athlete.shape}")
                start_date = datetime.date.today()
                end_date = start_date
                id = credentials_dict[keys_list[athletes_unified.index(athlete)]]["id"]

                wellness_data = download_data.wellness(start_date, end_date, id)
                wellness_df = clean_data.wellness_data(wellness_data)
                wellness_df.to_sql(f'wellness_daily_{athlete}', pool, schema='wellness_data', if_exists='append', index=False)
        except:
                logger.info(f"No hay datos para {athlete}")
                start_date = "2025-01-01"
                start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date = datetime.date.today()
                id = credentials_dict[keys_list[athletes_unified.index(athlete)]]["id"]
                logger.info(f"Descargabdo datos desde {start_date} hasta {end_date} para {athlete}")
                wellness_data_dict = download_data.wellness(start_date, end_date, id)
                wellness_df = clean_data.wellness_data(wellness_data_dict)
                query = text(f"CREATE TABLE IF NOT EXISTS wellness_data.wellness_daily_{athlete} (date DATE, rampRate FLOAT, weight FLOAT, restingHR FLOAT, hrv FLOAT, sleepSecs FLOAT, mood FLOAT, readinessMSA FLOAT, injury FLOAT);")
                with pool.begin() as conn:
                    conn.execute(query)
                wellness_df.to_sql(f'wellness_daily_{athlete}', pool, schema='wellness_data', if_exists='append', index=False)

def update_activities_data(pool, coach_id, api_key, coach_name, credentials_dict):
    download_data = Intervals(coach_id, api_key)
    clean_data = CleanData(coach_name)
    athletes_unified = []
    athletes = []
    keys_list = list(credentials_dict.keys())
    for key, data in credentials_dict.items():
        if 'icu_name' in data:
            name_unified = data['icu_name'].replace(" ", "_")
            athletes_unified.append(name_unified)
            athletes.append(data['icu_name'])
    logger.info(f"Atletas encontrados: {athletes}")

    # creata table
    for athlete in athletes_unified:
        logger.info(f"Guardando datos para {athlete}...")
        #if athlete == 'Mikel_Campo': # cambiar cuando ids del resto
        try:
                query = f"SELECT * FROM activities_data.activities_{athlete}"
                df_athlete = pd.read_sql(query, pool)
                logger.info(f"El shape es: {df_athlete.shape}")
                start_date = datetime.date.today()
                end_date = start_date
                id = credentials_dict[keys_list[athletes_unified.index(athlete)]]["id"]

                activities_data = download_data.activities(start_date, end_date, id)
                activities_df = clean_data.activities_data(activities_data)
                activities_df.to_sql(f'activities_{athlete}', pool, schema='activities_data', if_exists='append', index=False)
        except:
                logger.info(f"No hay datos para {athlete}")
                start_date = "2025-01-01"
                start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date = datetime.date.today()
                id = credentials_dict[keys_list[athletes_unified.index(athlete)]]["id"]
                logger.info(f"Descargabdo datos desde {start_date} hasta {end_date} para {athlete}")
                activities_data_dict = download_data.activities(start_date, end_date, id)
                activities_df = clean_data.activities_data(activities_data_dict)
                query = text(f"CREATE TABLE IF NOT EXISTS activities_data.activities_{athlete} (date DATE, rampRate FLOAT, weight FLOAT, restingHR FLOAT, hrv FLOAT, sleepSecs FLOAT, mood FLOAT, readinessMSA FLOAT, injury FLOAT);")
                with pool.begin() as conn:
                    conn.execute(query)
                activities_df.to_sql(f'activities_{athlete}', pool, schema='activities_data', if_exists='append', index=False)

@app.route("/")
def home():
    try:
        logger.info("\n" + "#"*60)
        logger.info("### PETICIÓN RECIBIDA DEL SCHEDULER ###")
        logger.info("#"*60 + "\n")
        
        project_id = "weeklytrainingemail"
        secret_id = "p-info-json"
        gc_credentials = GCcredential(project_id, secret_id)
        credentials_dict = gc_credentials.get_credentials_from_secret()
        gc_mysql = GCMySQL(credentials_dict)

        # update database
        for user, data in credentials_dict.items():
            try:
                if data['role'] == "coach":
                    coach_name = user
                    logger.info(f"Coach identificado: {coach_name}")
                
                    coach_id = credentials_dict[coach_name]["id"]
                    api_key = credentials_dict[coach_name]["password"]

            except:
                pass
        pool = gc_mysql.sqlalchemy_engine(db_name="weekly_stats")
        update_weekly_stats_data(pool, coach_id, api_key, coach_name, credentials_dict)
        update_weekly_stats_moving_averages(pool, coach_id, api_key, coach_name, credentials_dict)
        pool = gc_mysql.sqlalchemy_engine(db_name="wellness_data")
        update_weellness_daily_data(pool, coach_id, api_key, coach_name, credentials_dict)
        pool = gc_mysql.sqlalchemy_engine(db_name="activities_data")
        update_activities_data(pool, coach_id, api_key, coach_name, credentials_dict)
        
        logger.info("\n### Esperando 10 segundos antes de responder... ###")
        time.sleep(10)
        
        logger.info("### RESPUESTA ENVIADA AL SCHEDULER ###\n")
        return "Base de datos actualizada correctamente.", 200
        
    except Exception as e:
        import traceback
        logger.error(f"\n❌ ERROR EN EL ENDPOINT: {e}")
        logger.error(traceback.format_exc())
        return f"Error: {e}", 500

@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    
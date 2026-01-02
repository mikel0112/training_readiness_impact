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
            query_1 = f"DELETE FROM weekly_stats.weekly_stats_{athlete} WHERE date = '{start_date}'"
            query_2 = f"DELETE FROM weekly_stats.weekly_stats_{athlete} WHERE date = '{previous_week_data}'"
            # execute query
            with pool.begin() as conn:
                conn.execute(query_1)
                conn.execute(query_2)
            # download new data
            query = f"SELECT date FROM weekly_stats.weekly_stats_{athlete} ORDER BY date DESC"
            old_weekly_stats_df = pd.read_sql_query(query, pool)
            logger.info(f"Descargando datos desde {previous_week_data} hasta {end_date}...")
            weekly_stats_data = download_data.summary_stats(previous_week_data, end_date)
            logger.info("✓ Datos descargados")
                    
            logger.info(f"Guardando datos para {athlete}...")
            clean_data = CleanData(athletes[athletes_unified.index(athlete)])
            df_weekly_stats = clean_data.weekly_stats_data(weekly_stats_data, athlete, old_weekly_stats_df)
            logger.info(f"El index es: {df_weekly_stats.index}")
            # create table
            df_weekly_stats.to_sql(f'weekly_stats_{athlete}', pool, if_exists='append', index=False)
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

            end_date = datetime.date.today() - datetime.timedelta(days=2)
            logger.info(f"Fecha fin: {end_date}")
            
            start_date = end_date - datetime.timedelta(days=366)
            old_weekly_stats_df = pd.DataFrame()
            logger.info(f"Archivo nuevo. Descargando últimos 366 días desde: {start_date}")
            
            if start_date <= end_date:
                logger.info(f"Descargando datos desde {start_date} hasta {end_date}...")
                weekly_stats_data = download_data.summary_stats(start_date, end_date)
                logger.info("✓ Datos descargados")
                
                # save data for every athlete
                clean_data = CleanData(coach_name)
                for athl in athletes:
                    logger.info(f"Guardando datos para {athl}...")
                    df_weekly_stats = clean_data.weekly_stats_data(weekly_stats_data, athl, old_weekly_stats_df)
                    df_columns = df_weekly_stats.columns.tolist()
                    # create table
                    df_weekly_stats.to_sql(f'weekly_stats_{athletes_unified[athletes.index(athl)]}', pool, if_exists='append', index=False)
                break
            else:
                logger.info("No hay nuevos datos para descargar")
                break

def update_weekly_stats_moving_averages(pool, coach_id, api_key, coach_name):
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
    query = f"CREATE TABLE IF NOT EXISTS weekly_stats.weekly_stats_moving_averages ({table_columns})"
    pd.read_sql_query(query, pool)

    # update weekly_stats_moving_averages table

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
        connector = gc_mysql.get_db_connection()
        pool = gc_mysql.sqlalchemy_engine()

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
        update_weekly_stats_data(pool, coach_id, api_key, coach_name, credentials_dict)
        
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
    
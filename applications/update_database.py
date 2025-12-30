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




logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def update_weekly_stats_data(pool, coach_id, api_key, coach_name):
    logger.info("Comprobando si existen datos en la base de datos...")
    # list of athletes
    athletes = []
    athletes_unified = []
    for athlete, data in credentials_dict.items():
        if 'icu_name' in data:
            name_unified = data['icu_name'].replace(" ", "_")
            athletes_unified.append(name_unified)
            athletes.append(athlete)
    logger.info(f"Atletas encontrados: {athletes}")
    download_data = Intervals(coach_id, api_key)
    try:
        for athlete in athletes_unified:
            # extract latest date in any of the tables
            logger.info(f"Buscando datos para {athlete} en la base de datos...")
            query = f"SELECT date FROM weekly_stats.weekly_stats_{athlete} ORDER BY date DESC LIMIT 1"
            result = pd.read_sql_query(query, pool)
            start_date = datetime.date.fromisoformat(result['date'].values[0])
            end_date = datetime.date.today()
            if start_date <= end_date:
                logger.info(f"Descargando datos desde {start_date} hasta {end_date}...")
                weekly_stats_data = download_data.summary_stats(start_date, end_date)
                logger.info("✓ Datos descargados")
                
                # save data for every athlete
                clean_data = CleanData(coach_name)
                for athlete in athletes:
                    logger.info(f"Guardando datos para {athlete}...")
                    query = f"SELECT * FROM weekly_stats.weekly_stats_{athletes_unified[athletes.index(athlete)]}"
                    old_weekly_stats_df = pd.read_sql_query(query, pool)
                    df_weekly_stats = clean_data.weekly_stats_data(weekly_stats_data, athlete, old_weekly_stats_df)
                    df_columns = df_weekly_stats.columns.tolist()
                    # create table
                    df_weekly_stats.to_sql(f'weekly_stats_{athletes_unified[athletes.index(athlete)]}', pool, if_exists='append', index=False)
            else:
                logger.info("No hay nuevos datos para descargar")
            logger.info(f"✓ Datos existentes en la base de datos para {athlete}")

    except Exception as e:
        logger.info("No existen datos en la base de datos")
        logger.info(f"Error al consultar la base de datos: {e}")
        logger.info("Descargando estadísticas semanales...")
        ########-------------------------------------########
        ########      DOWNLOAD WEEKLY STATS DATA     ########
        ########-------------------------------------########
        logger.info("Descargando estadísticas semanales...")
        end_date = datetime.date.today()
        logger.info(f"Fecha fin: {end_date}")
        
        start_date = end_date - datetime.timedelta(days=30)
        old_weekly_stats_df = pd.DataFrame()
        logger.info(f"Archivo nuevo. Descargando últimos 30 días desde: {start_date}")
        
        if start_date <= end_date:
            logger.info(f"Descargando datos desde {start_date} hasta {end_date}...")
            weekly_stats_data = download_data.summary_stats(start_date, end_date)
            logger.info("✓ Datos descargados")
            
            # save data for every athlete
            clean_data = CleanData(coach_name)
            for athlete in athletes:
                logger.info(f"Guardando datos para {athlete}...")
                df_weekly_stats = clean_data.weekly_stats_data(weekly_stats_data, athlete, old_weekly_stats_df)
                df_columns = df_weekly_stats.columns.tolist()
                # create table
                df_weekly_stats.to_sql(f'weekly_stats_{athletes_unified[athletes.index(athlete)]}', pool, if_exists='append', index=False)
        else:
            logger.info("No hay nuevos datos para descargar")


if __name__ == "__main__":
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
    update_weekly_stats_data(pool, coach_id, api_key, coach_name)
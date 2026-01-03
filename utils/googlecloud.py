from google.cloud import secretmanager
from google.cloud import storage
from google.cloud.sql.connector import Connector
from io import StringIO
import logging
import json
import pandas as pd
import os
import pymysql
import sqlalchemy


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GCcredential():
    def __init__(self, project_id, secret_id):
        self._client = secretmanager.SecretManagerServiceClient()
        self._name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    
    def get_credentials_from_secret(self):
        """Lee las credenciales desde Google Secret Manager"""
        try:
            response = self._client.access_secret_version(request={"name": self._name})
            secret_data = response.payload.data.decode("UTF-8")
            return json.loads(secret_data)
        except Exception as e:
            logger.error(f"Error al leer credenciales desde Secret Manager: {e}")
            raise

class GCStorage():

    def __init__(self, bucket_name):
        self._client = storage.Client()
        self._bucket = self._client.bucket(bucket_name)
    
    def read_csv_from_gcs(self, blob_path):
        """Lee un CSV desde Cloud Storage"""
        try:
            blob = self._bucket.blob(blob_path)
            if blob.exists():
                content = blob.download_as_string()
                return pd.read_csv(StringIO(content.decode('utf-8')))
            else:
                logger.info(f"Archivo {blob_path} no existe en GCS")
                return None
        except Exception as e:
            logger.error(f"Error al leer {blob_path} desde GCS: {e}")
            return None

    def save_csv_to_gcs(self, df, blob_path):
        """Guarda un DataFrame como CSV en Cloud Storage"""
        try:
            blob = self._bucket.blob(blob_path)
            csv_string = df.to_csv(index=False)
            blob.upload_from_string(csv_string, content_type='text/csv')
            logger.info(f"✓ CSV guardado en GCS: {blob_path}")
        except Exception as e:
            logger.error(f"Error al guardar {blob_path} en GCS: {e}")
            raise

class GCMySQL():
    def __init__(self, gc_credentials):
        self._credentials = gc_credentials
    
    def get_db_user_info(self):
        self.db_user = self._credentials['database']['user']
        self.db_password = self._credentials['database']['password'] 

    def get_db_connection(self, db_name):
        project_id = "weeklytrainingemail"
        region = "europe-southwest1"
        instance_name = "weekyemail"
        self.get_db_user_info()
        db_user = self.db_user
        db_password = self.db_password
        connection_name = f"{project_id}:{region}:{instance_name}"

        connector = Connector()

        conn = connector.connect(
            connection_name,
            "pymysql",
            user=db_user,
            password=db_password,
            db=db_name,
        )

        return conn
    
    def sqlalchemy_engine(self):
        engine = sqlalchemy.create_engine("mysql+pymysql://", creator=self.get_db_connection)
        return engine
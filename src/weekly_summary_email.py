import os
from fpdf import FPDF
from redmail import gmail
import matplotlib.pyplot as plt
import json
import pandas as pd
import datetime
import numpy as np
import sys
import logging
from google.cloud import secretmanager
from down_data_intervals import Intervals, SaveData, read_csv_from_gcs, save_csv_to_gcs
from flask import Flask
import threading
import time


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_credentials_from_secret():
    """Lee las credenciales desde Google Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = "weeklytrainingemail"
        secret_id = "p-info-json"
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        
        response = client.access_secret_version(request={"name": name})
        secret_data = response.payload.data.decode("UTF-8")
        return json.loads(secret_data)
    except Exception as e:
        logger.error(f"Error al leer credenciales desde Secret Manager: {e}")
        raise

# Esto le dice a Python que busque archivos en la carpeta actual del script
dir_actual = os.path.dirname(os.path.abspath(__file__))
if dir_actual not in sys.path:
    sys.path.append(dir_actual)


app = Flask(__name__)

class ReporteDeportista(FPDF):

    def __init__(self, athlete_name):
        super().__init__()
        self.athlete_name = athlete_name

    def header(self):
        self.set_font("helvetica", "B", 15)
        self.cell(0, 10, f"Resumen de Rendimiento: {self.athlete_name}", 0, 1, "C")
        self.ln(5)

def generar_pdf_deportista(nombre_archivo, athlete_name):
        pdf = ReporteDeportista(athlete_name)
        pdf.add_page()
        pdf.set_font("helvetica", size=12)

        # Introducción
        pdf.multi_cell(0, 10, "Hola,\nAquí tienes el análisis visual y las estadísticas correspondientes a la última sesión. Los datos muestran un progreso constante.")
        pdf.ln(5)

        # Listado de imágenes a incluir
        graficos = [
            ("1. Intensidad de Entrenamiento", f"outputs/{athlete_name}/email/form.png"),
            ("2. Comparativa Semanal", f"outputs/{athlete_name}/email/hours.png"),
            ("3. Distribución de Zonas", f"outputs/{athlete_name}/email/zones.png")
        ]

        for titulo, ruta in graficos:
            if os.path.exists(ruta):
                pdf.set_font("helvetica", "B", 12)
                pdf.cell(0, 10, titulo, 0, 1)
                
                # Insertar imagen (ajustando ancho a 180mm)
                pdf.image(ruta, x=15, w=180)
                pdf.ln(10)

        pdf.output(nombre_archivo)

class WriteEmail():
    def __init__(self, athlete_name, date):
        self.athlete_name = athlete_name
        self.date = date
        # Leer CSV desde GCS
        csv_path = f"data/{self.athlete_name}/weekly_stats.csv"
        self.data = read_csv_from_gcs(csv_path)
        if self.data is None:
            raise FileNotFoundError(f"No se encontró {csv_path} en Cloud Storage")
    
    def form_chart(self):
        form = self.data['form'].loc[self.data["date"] == self.date].values[0]
        # fill the back space with different colors based on y values horizontally
        fig = plt.figure(figsize=(10, 5))
        ax = fig.add_subplot(1, 1, 1)
        # dar color al fondo de la grafica
        ax.axhspan(-100, -30, facecolor='red', alpha=0.5)
        ax.axhspan(-30, -10, facecolor='green', alpha=0.5)
        ax.axhspan(-10, 5, facecolor='gray', alpha=0.5)
        ax.axhspan(5, 20, facecolor='blue', alpha=0.5)
        ax.axhspan(20, 100, facecolor='yellow', alpha=0.5)

        # graph the form bar vertically
        ax.bar(1, form, color='black', width=0.5)
        ax.set_xlim(0, 2)
        ax.set_ylim(-100, 100)
        ax.set_yticks([-100, -30, -10, 5, 20, 100])
        ax.set_yticklabels(['-100', '-30', '-10', '5', '20', '100'])
        ax.set_xticks([])
        ax.set_xticklabels([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        os.makedirs(f"outputs/{self.athlete_name}/email",exist_ok=True)
        plt.savefig(f"outputs/{self.athlete_name}/email/form.png", bbox_inches='tight')
        plt.close()
    
    def hours_pie_chart(self):
        labels = 'Run', 'Ride', 'Other'
        run_hours = self.data['run_time'].loc[self.data["date"] == self.date].values[0]
        ride_hours = self.data['ride_time'].loc[self.data["date"] == self.date].values[0]
        other_hours = self.data['strength_time'].loc[self.data["date"] == self.date].values[0]
        sizes = [run_hours, ride_hours, other_hours]
        # if value nan convert to 0 use numpy
        sizes = np.nan_to_num(sizes)
        explode = (0, 0, 0.1)
        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                shadow=True, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.savefig(f"outputs/{self.athlete_name}/email/hours.png", bbox_inches='tight')
        plt.close()
    
    def zones_cumulative_bar_chart(self):
        z1_per = self.data['Z_1'].loc[self.data["date"] == self.date].values[0]
        z2_per = self.data['Z_2'].loc[self.data["date"] == self.date].values[0]
        z3_per = self.data['Z_3'].loc[self.data["date"] == self.date].values[0]
        z4_per = self.data['Z_4'].loc[self.data["date"] == self.date].values[0]
        z5_per = self.data['Z_5'].loc[self.data["date"] == self.date].values[0]
        z6_per = self.data['Z_6'].loc[self.data["date"] == self.date].values[0]
        z7_per = self.data['Z_7'].loc[self.data["date"] == self.date].values[0]

        # graph in bars each in a personalizeed color
        plt.figure(figsize=(10, 5))
        plt.bar(['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Zone 6', 'Zone 7'], 
                [z1_per, z2_per, z3_per, z4_per, z5_per, z6_per, z7_per], 
                color=['red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink'])
        plt.savefig(f"outputs/{self.athlete_name}/email/zones.png", bbox_inches='tight')
        plt.close()

    def send_email(self, info, athlete_name, date, coach_name):
        try:
            logger.info(f"[INICIO] Preparando email para {athlete_name}")
            
            logger.info("Generando gráfico de forma...")
            self.form_chart()
            logger.info("✓ Gráfico de forma generado")
            
            logger.info("Generando gráfico de horas...")
            self.hours_pie_chart()
            logger.info("✓ Gráfico de horas generado")
            
            logger.info("Generando gráfico de zonas...")
            self.zones_cumulative_bar_chart()
            logger.info("✓ Gráfico de zonas generado")

            # pdf
            athlete_name_unified = athlete_name.replace(" ", "_")
            pdf_output = f"outputs/{athlete_name}/email/{date}.pdf"
            logger.info(f"Generando PDF: {pdf_output}")
            generar_pdf_deportista(pdf_output, athlete_name)
            logger.info(f"✓ PDF generado correctamente")

            with open(pdf_output, "rb") as f:
                contenido_pdf = f.read()
            logger.info(f"✓ PDF leído, tamaño: {len(contenido_pdf)} bytes")
            
            # email
            gmail.user_name = info[coach_name]["email"]
            gmail.password = info[coach_name]["email_pass"]
            logger.info(f"Configurando Gmail con usuario: {gmail.user_name}")

            for key,values in info.items():
                if values['icu_name'] == athlete_name:
                    #correo = values['email']
                    correo = 'mikelcampo0112@gmail.com'
                    logger.info(f"Email destino encontrado: {correo}")
            
            logger.info(f"Enviando email a {correo}...")
            gmail.send(
                subject="Estadísticas semanales de " + athlete_name,
                receivers=[correo],
                html=f"<p>Hola {athlete_name}, adjunto encontrarás tu reporte de rendimiento en PDF.</p>",
                attachments={
                    "Reporte_Rendimiento.pdf": contenido_pdf
                }
            )
            logger.info(f"✓✓✓ EMAIL ENVIADO EXITOSAMENTE a {athlete_name} ✓✓✓")
            
        except Exception as e:
            import traceback
            logger.error(f"❌ ERROR al enviar email a {athlete_name}: {e}")
            logger.error(traceback.format_exc())
            raise

def ejecutar_proceso_completo():
    try:
        logger.info("="*60)
        logger.info("INICIANDO PROCESO DE DATOS Y ENVÍO")
        logger.info("="*60)
        
        # get credentials from Secret Manager
        logger.info("Cargando credenciales desde Secret Manager...")
        credentials_info = get_credentials_from_secret()
        logger.info("✓ Credenciales cargadas exitosamente")
        
        for user, data in credentials_info.items():
            if data['role'] == "coach":
                coach_name = user
                logger.info(f"Coach identificado: {coach_name}")
        
        coach_id = credentials_info[coach_name]["id"]
        api_key = credentials_info[coach_name]["password"]

        intervals = Intervals(coach_id, api_key)
        save_data = SaveData(coach_name)
        logger.info("✓ Objetos Intervals y SaveData creados")

        ########-------------------------------------########
        ########      DOWNLOAD WEEKLY STATS DATA     ########
        ########-------------------------------------########
        logger.info("Descargando estadísticas semanales...")
        today_date = datetime.date.today()
        end_date = today_date - datetime.timedelta(days=today_date.weekday()) - datetime.timedelta(days=1)
        logger.info(f"Fecha fin: {end_date}")
        
        # Leer datos existentes desde GCS
        weekly_stats_path = f"data/{coach_name}/weekly_stats.csv"
        old_weekly_stats_df = read_csv_from_gcs(weekly_stats_path)
        
        if old_weekly_stats_df is not None and not old_weekly_stats_df.empty:
            try:
                start_date = pd.to_datetime(old_weekly_stats_df['date'].max()) + datetime.timedelta(days=1)
                logger.info(f"Archivo existente encontrado en GCS. Fecha inicio: {start_date}")
            except Exception as e:
                logger.warning(f"Error al procesar fecha: {e}. Descargando últimos 90 días...")
                start_date = end_date - datetime.timedelta(days=90)
                old_weekly_stats_df = pd.DataFrame()
        else:
            start_date = end_date - datetime.timedelta(days=90)
            old_weekly_stats_df = pd.DataFrame()
            logger.info(f"Archivo nuevo. Descargando últimos 90 días desde: {start_date}")
        
        if start_date <= end_date:
            logger.info(f"Descargando datos desde {start_date} hasta {end_date}...")
            weekly_stats_data = intervals.summary_stats(start_date, end_date)
            logger.info("✓ Datos descargados")
            
            # list of athletes
            athletes = []
            for athlete, data in credentials_info.items():
                if 'icu_name' in data:
                    athletes.append(data['icu_name'])
            logger.info(f"Atletas encontrados: {athletes}")
            
            # save data for every athlete
            for athlete in athletes:
                logger.info(f"Guardando datos para {athlete}...")
                save_data.weekly_stats_data(weekly_stats_data, athlete, old_weekly_stats_df)
                logger.info(f"✓ Datos guardados para {athlete}")
        else:
            logger.info("No hay nuevos datos para descargar")

        #---------------------------------------------------#
        #---------------------------------------------------#
        logger.info("\n" + "="*60)
        logger.info("INICIANDO ENVÍO DE EMAILS")
        logger.info("="*60)
        
        date = datetime.datetime.today() - datetime.timedelta(days=datetime.datetime.today().weekday()) - datetime.timedelta(days=7)
        date_string = date.strftime("%Y-%m-%d")
        logger.info(f"Fecha de reporte: {date_string}")
        
        email_count = 0
        for key, values in credentials_info.items():
            if values['role']=='coach':
                coach_name = key
            if 'icu_name' in values:
                athlete_name = values['icu_name']
                logger.info(f"\n--- Procesando atleta #{email_count+1}: {athlete_name} ---")
                email_com = WriteEmail(athlete_name, date_string)
                email_com.send_email(credentials_info, athlete_name, date_string, coach_name)
                email_count += 1
                logger.info(f"--- Finalizado atleta {athlete_name} ---\n")

        logger.info("="*60)
        logger.info(f"✓✓✓ PROCESO FINALIZADO CON ÉXITO - {email_count} emails enviados ✓✓✓")
        logger.info("="*60)
        
    except Exception as e:
        import traceback
        logger.error("="*60)
        logger.error("❌❌❌ ERROR EN EL PROCESO ❌❌❌")
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
        logger.error("="*60)
        raise

@app.route("/")
def home():
    try:
        logger.info("\n" + "#"*60)
        logger.info("### PETICIÓN RECIBIDA DEL SCHEDULER ###")
        logger.info("#"*60 + "\n")
        
        ejecutar_proceso_completo()
        
        logger.info("\n### Esperando 10 segundos antes de responder... ###")
        time.sleep(10)
        
        logger.info("### RESPUESTA ENVIADA AL SCHEDULER ###\n")
        return "Emails enviados correctamente.", 200
        
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
    logger.info(f"Iniciando Flask app en puerto {port}")
    app.run(host='0.0.0.0', port=port)
from fpdf import FPDF
from redmail import gmail
from utils.googlecloud import GCcredential, GCMySQL
from flask import Flask
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import numpy as np
import sys
import logging
import time
import os


# Configurar logging
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

class ReporteDeportista(FPDF):

    def __init__(self, athlete_name):
        super().__init__()
        self.athlete_name = athlete_name

    def header(self):
        self.set_font("helvetica", "B", 15)
        self.cell(0, 10, f"Resumen de Rendimiento: {self.athlete_name}", 0, 1, "C")
        self.ln(5)

def generar_pdf_athlete_deportista(nombre_archivo, athlete_name):
        pdf_athlete = ReporteDeportista(athlete_name)
        pdf_athlete.add_page()
        pdf_athlete.set_font("helvetica", size=12)

        # Introducción
        pdf_athlete.multi_cell(0, 10, "Hola,\nAquí tienes el análisis visual y las estadísticas correspondientes a la última semana.")
        pdf_athlete.ln(5)

        # Listado de imágenes a incluir
        graficos = [
            ("Gráfico de forma", f"outputs/{athlete_name}/email/form.png"),
            ("Gráfico de horas", f"outputs/{athlete_name}/email/hours.png"),
            ("Gráfico de zonas", f"outputs/{athlete_name}/email/zones.png"),
            ("Gráfico de desnivel", f"outputs/{athlete_name}/email/elevation.png"),
            ("Gráfico de volumen", f"outputs/{athlete_name}/email/volume.png"),
        ]

        for titulo, ruta in graficos:
            if os.path.exists(ruta):
                pdf_athlete.set_font("helvetica", "B", 12)
                pdf_athlete.cell(0, 10, titulo, 0, 1)
                
                # Insertar imagen (ajustando ancho a 180mm)
                pdf_athlete.image(ruta, x=15, w=180)
                pdf_athlete.ln(10)

        pdf_athlete.output(nombre_archivo)

class WriteEmail():
    def __init__(self, athlete_name, date, data, df_average):
        self.athlete_name = athlete_name
        self.date = date
        self.athlete_data = data
        self.mov_avg_data = df_average
    
    def form_chart(self):
        form = self.athlete_data['form'].values[0]
        if form < -30:
            bar_color = 'red'
        elif form < -10:
            bar_color = 'green'
        elif form < 5:
            bar_color = 'gray'
        elif form < 20:
            bar_color = 'blue'
        else:
            bar_color = 'yellow'
        plt.figure(figsize=(10, 5))
        plt.bar([0.5], [form], color=bar_color, label='Form')
        
        # add horizontal lines
        plt.axhline(y=-30, color='red', linestyle='solid', label='Riesgo Alto')
        plt.axhline(y=-10, color='green', linestyle='solid', label='Óptimo')
        plt.axhline(y=5, color='gray', linestyle='solid', label = 'Zona gris')
        plt.axhline(y=20, color='blue', linestyle='solid', label = 'Fresco')
        plt.axhline(y=100, color='yellow', linestyle='solid', label = 'Transición')

        
        # fill the back space with different colors based on y values horizontally
        plt.fill_between([0, 1], -30, -100, color='lightcoral')
        plt.fill_between([0, 1], -10, -30, color='yellowgreen')
        plt.fill_between([0, 1], 5, -10, color='lightgray')
        plt.fill_between([0, 1], 20, 5, color='lightblue')
        plt.fill_between([0, 1], 100, 20, color='lightyellow')

        # add legend
        plt.legend()

        # add labels
        plt.ylabel('Form')
        plt.title('Impacto de la carga de entrenamiento', fontsize=16, fontweight='bold')
        
        os.makedirs(f"outputs/{self.athlete_name}/email",exist_ok=True)
        if os.path.exists(f"outputs/{self.athlete_name}/email/form.png"):
            os.remove(f"outputs/{self.athlete_name}/email/form.png")
        plt.savefig(f"outputs/{self.athlete_name}/email/form.png", bbox_inches='tight')
        plt.close()
    
    def hours_pie_chart(self):
        labels = 'Run', 'Ride', 'Other'
        run_hours = self.athlete_data['run_time'].values[0]
        ride_hours = self.athlete_data['ride_time'].values[0]
        other_hours = self.athlete_data['strength_time'].values[0]
        sizes = [run_hours, ride_hours, other_hours]
        # if value nan convert to 0 use numpy
        sizes = np.array(sizes, dtype=float)
        sizes = np.nan_to_num(sizes)
        logger.info(F"sizes: {sizes}")
        explode = (0, 0, 0.1)
        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                shadow=True, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        # add title
        ax1.set_title('Distribución de Horas por Actividad', fontsize=16, fontweight='bold')
        if os.path.exists(f"outputs/{self.athlete_name}/email/hours.png"):
            os.remove(f"outputs/{self.athlete_name}/email/hours.png")
        plt.savefig(f"outputs/{self.athlete_name}/email/hours.png", bbox_inches='tight')
        plt.close()
    
    def zones_cumulative_bar_chart(self):

        z1_per = self.athlete_data['Z_1'].values[0]
        z2_per = self.athlete_data['Z_2'].values[0]
        z3_per = self.athlete_data['Z_3'].values[0]
        z4_per = self.athlete_data['Z_4'].values[0]
        z5_per = self.athlete_data['Z_5'].values[0]
        z6_per = self.athlete_data['Z_6'].values[0]


        # graph in bars each in a personalizeed color
        plt.figure(figsize=(10, 5))
        plt.bar(['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Zone 6'], 
                [z1_per, z2_per, z3_per, z4_per, z5_per, z6_per], 
                color=['gray', 'green', 'yellow', 'red', 'purple', 'black'])
        # add the value in each bar
        for i, v in enumerate([z1_per, z2_per, z3_per, z4_per, z5_per, z6_per]):
            plt.text(i, v, str(v), ha='center', va='bottom', fontsize=8)
        plt.xlabel('Zones')
        plt.ylabel('Percentage')
        plt.title('Distribución de Intensidad', fontsize=16, fontweight='bold')
        if os.path.exists(f"outputs/{self.athlete_name}/email/zones.png"):
            os.remove(f"outputs/{self.athlete_name}/email/zones.png")
        plt.savefig(f"outputs/{self.athlete_name}/email/zones.png", bbox_inches='tight')
        plt.close()
    
    def elev_gain_chart(self):

        # extract the averages but just for the self.athlete_name
        elev_avg_4 = self.mov_avg_data.loc[self.mov_avg_data['Athlete'] == self.athlete_name]['MA_elevation_4w'].values[0]
        elev_avg_12 = self.mov_avg_data.loc[self.mov_avg_data['Athlete'] == self.athlete_name]['MA_elevation_12w'].values[0]
        elev_avg_52 = self.mov_avg_data.loc[self.mov_avg_data['Athlete'] == self.athlete_name]['MA_elevation_52w'].values[0]
        week_elev = self.athlete_data['total_elevation_gain'].values[0]

        plt.figure(figsize=(10, 5))
        plt.bar(['Desnivel/Semana'], [week_elev], color='green', label='Desnivel Semana Actual')

        plt.axhline(y=elev_avg_4, color='red', linestyle='solid', label='Desnivel Medio Últimos 4 Semanas')
        plt.axhline(y=elev_avg_12, color='blue', linestyle='dotted', label='Desnivel Medio Últimas 3 meses')
        plt.axhline(y=elev_avg_52, color='black', linestyle='dashed', label='Desnivel Medio Último año')

        # add title and labels
        plt.title('Comparativa desnivel', fontsize=16, fontweight='bold')
        plt.ylabel('Desnivel (m)')
        plt.legend()

        if os.path.exists(f"outputs/{self.athlete_name}/email/elevation.png"):
            os.remove(f"outputs/{self.athlete_name}/email/elevation.png")
        plt.savefig(f"outputs/{self.athlete_name}/email/elevation.png", bbox_inches='tight')
        plt.close()
    
    def time_chart(self):

        # extract the averages but just for the self.athlete_name
        time_avg_4 = self.mov_avg_data.loc[self.mov_avg_data['Athlete'] == self.athlete_name]['MA_time_4w'].values[0]
        time_avg_12 = self.mov_avg_data.loc[self.mov_avg_data['Athlete'] == self.athlete_name]['MA_time_12w'].values[0]
        time_avg_52 = self.mov_avg_data.loc[self.mov_avg_data['Athlete'] == self.athlete_name]['MA_time_52w'].values[0]
        week_time = self.athlete_data['time'].values[0]

        plt.figure(figsize=(10, 5))
        plt.bar(['Tiempo/Semana'], [week_time], color='green', label='Tiempo Semana Actual')

        plt.axhline(y=time_avg_4, color='red', linestyle='solid', label='Tiempo Medio Últimos 4 Semanas')
        plt.axhline(y=time_avg_12, color='blue', linestyle='dotted', label='Tiempo Medio Últimas 3 meses')
        plt.axhline(y=time_avg_52, color='black', linestyle='dashed', label='Tiempo Medio Último año')

        # add title and labels
        plt.title('Comparativa tiempo', fontsize=16, fontweight='bold')
        plt.ylabel('Tiempo (horas)')
        plt.legend()

        if os.path.exists(f"outputs/{self.athlete_name}/email/volume.png"):
            os.remove(f"outputs/{self.athlete_name}/email/volume.png")
        plt.savefig(f"outputs/{self.athlete_name}/email/volume.png", bbox_inches='tight')
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

            logger.info("Generando gráfico de desnivel...")
            self.elev_gain_chart()
            logger.info("✓ Gráfico de desnivel generado")

            logger.info("Generando gráfico de volumen...")
            self.time_chart()
            logger.info("✓ Gráfico de volumen generado")

            # pdf_athlete
            athlete_name_unified = athlete_name.replace(" ", "_")
            pdf_athlete_output = f"outputs/{athlete_name}/email/{date}.pdf"
            logger.info(f"Generando Pdf_athlete: {pdf_athlete_output}")
            # convert str to datetime date
            date = datetime.date.fromisoformat(date)
            last_pdf_athlete_date = date - datetime.timedelta(days=7)
            # convert date to str
            last_pdf_athlete_date = last_pdf_athlete_date.strftime("%Y-%m-%d")
            if os.path.exists(f"outputs/{athlete_name}/email/{last_pdf_athlete_date}.pdf"):
                os.remove(f"outputs/{athlete_name}/email/{last_pdf_athlete_date}.pdf")
            generar_pdf_athlete_deportista(pdf_athlete_output, athlete_name)
            logger.info(f"✓ Pdf_athlete generado correctamente")

            with open(pdf_athlete_output, "rb") as f:
                contenido_pdf_athlete = f.read()
            logger.info(f"✓ Pdf_athlete leído, tamaño: {len(contenido_pdf_athlete)} bytes")
            
            # email
            gmail.user_name = info[coach_name]["email"]
            gmail.password = info[coach_name]["email_pass"]
            logger.info(f"Configurando Gmail con usuario: {gmail.user_name}")

            for key,values in info.items():
                if 'icu_name' in values.keys():
                    if values['icu_name'] == athlete_name:
                        correo = values['email']
                        #correo = 'mikelcampo0112@gmail.com'
                        logger.info(f"Email destino encontrado: {correo}")
            
            logger.info(f"Enviando email a {correo}...")
            gmail.send(
                subject="Estadísticas semanales de " + athlete_name,
                receivers=[correo],
                html=f"<p>Hola {athlete_name}, adjunto encontrarás tu reporte de rendimiento en Pdf_athlete.</p>",
                attachments={
                    "Reporte_Rendimiento.pdf_athlete": contenido_pdf_athlete
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
        project_id = "weeklytrainingemail"
        secret_id = "p-info-json"
        gc_credential = GCcredential(project_id, secret_id)
        credentials_info = gc_credential.get_credentials_from_secret()
        logger.info("✓ Credenciales cargadas exitosamente")

        gc_mysql = GCMySQL(credentials_info)
        pool = gc_mysql.sqlalchemy_engine(db_name="weekly_stats")        

        #---------------------------------------------------#
        #---------------------------------------------------#
        logger.info("\n" + "="*60)
        logger.info("INICIANDO ENVÍO DE EMAILS")
        logger.info("="*60)
        
        date = datetime.datetime.today() - datetime.timedelta(days=7) 
        date_string = date.strftime("%Y-%m-%d")
        #date_string = '2025-12-29'
        logger.info(f"Fecha de reporte: {date_string}")
        
        email_count = 0
        for key, values in credentials_info.items():
            if 'role' in values:
                if values['role']=='coach':
                    coach_name = key
                if 'icu_name' in values.keys():
                    athlete_name = values['icu_name']
                    name_unified = athlete_name.replace(" ", "_")
                    logger.info(f"\n--- Procesando atleta #{email_count+1}: {athlete_name} ---")
                    # query data from athlete
                    query = f"SELECT * FROM weekly_stats.weekly_stats_{name_unified} WHERE date = '{date_string}'"
                    df_athlete = pd.read_sql_query(query, pool)
                    query = f"SELECT * FROM weekly_stats.weekly_stats_moving_averages"
                    df_averages = pd.read_sql_query(query, pool)
                    # if no data, skip
                    if df_athlete['time'].values[0] == 0.0:
                        logger.info(f"--- Atleta {athlete_name} sin datos ---")
                        continue
                    else:
                        logger.info(f"--- Atleta {athlete_name} con datos ---")
                        email_com = WriteEmail(athlete_name, date_string, df_athlete, df_averages)
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
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
    def __init__(self, athlete_name, date, data):
        self.athlete_name = athlete_name
        self.date = date
        self.data = self.data
    
    def form_chart(self):
        form = self.data['form'].values[0]
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
        if os.path.exists(f"outputs/{self.athlete_name}/email/form.png"):
            os.remove(f"outputs/{self.athlete_name}/email/form.png")
        plt.savefig(f"outputs/{self.athlete_name}/email/form.png", bbox_inches='tight')
        plt.close()
    
    def hours_pie_chart(self):
        labels = 'Run', 'Ride', 'Other'
        run_hours = self.data['run_time'].values[0]
        ride_hours = self.data['ride_time'].values[0]
        other_hours = self.data['strength_time'].values[0]
        sizes = [run_hours, ride_hours, other_hours]
        # if value nan convert to 0 use numpy
        sizes = np.nan_to_num(sizes)
        explode = (0, 0, 0.1)
        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                shadow=True, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        if os.path.exists(f"outputs/{self.athlete_name}/email/hours.png"):
            os.remove(f"outputs/{self.athlete_name}/email/hours.png")
        plt.savefig(f"outputs/{self.athlete_name}/email/hours.png", bbox_inches='tight')
        plt.close()
    
    def zones_cumulative_bar_chart(self):
        z1_per = self.data['Z_1'].values[0]
        z2_per = self.data['Z_2'].values[0]
        z3_per = self.data['Z_3'].values[0]
        z4_per = self.data['Z_4'].values[0]
        z5_per = self.data['Z_5'].values[0]
        z6_per = self.data['Z_6'].values[0]
        z7_per = self.data['Z_7'].values[0]

        # graph in bars each in a personalizeed color
        plt.figure(figsize=(10, 5))
        plt.bar(['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Zone 6', 'Zone 7'], 
                [z1_per, z2_per, z3_per, z4_per, z5_per, z6_per, z7_per], 
                color=['red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink'])
        if os.path.exists(f"outputs/{self.athlete_name}/email/zones.png"):
            os.remove(f"outputs/{self.athlete_name}/email/zones.png")
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
            last_pdf_date = date - datetime.timedelta(days=7)
            if os.path.exists(f"outputs/{athlete_name}/email/{last_pdf_date}.pdf"):
                os.remove(f"outputs/{athlete_name}/email/{last_pdf_date}.pdf")
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
        project_id = "weeklytrainingemail"
        secret_id = "p-info-json"
        gc_credential = GCcredential(project_id, secret_id)
        credentials_info = gc_credential.get_credentials_from_secret()
        logger.info("✓ Credenciales cargadas exitosamente")
        
        for user, data in credentials_info.items():
            if data['role']:
                if data['role'] == "coach":
                    coach_name = user
                    logger.info(f"Coach identificado: {coach_name}")
        
        coach_id = credentials_info[coach_name]["id"]
        api_key = credentials_info[coach_name]["password"]

        gc_mysql = GCMySQL(credentials_info)
        connector = gc_mysql.get_db_connection()
        pool = gc_mysql.sqlalchemy_engine()        

        #---------------------------------------------------#
        #---------------------------------------------------#
        logger.info("\n" + "="*60)
        logger.info("INICIANDO ENVÍO DE EMAILS")
        logger.info("="*60)
        
        date = datetime.datetime.today() - datetime.timedelta(days=6)
        date_string = date.strftime("%Y-%m-%d")
        logger.info(f"Fecha de reporte: {date_string}")
        
        email_count = 0
        for key, values in credentials_info.items():
            if values['role']=='coach':
                coach_name = key
            if 'icu_name' in values:
                athlete_name = values['icu_name']
                name_unified = athlete_name.replace(" ", "_")
                logger.info(f"\n--- Procesando atleta #{email_count+1}: {athlete_name} ---")
                # query data from athlete
                query = f"SELECT * FROM weekly_stats.weekly_stats_{name_unified} WHERE date = '{date_string}'"
                df = pd.read_sql_query(query, pool)
                email_com = WriteEmail(athlete_name, date_string, df)
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
import os
from fpdf import FPDF
from redmail import gmail
import matplotlib.pyplot as plt
import json
import pandas as pd
import datetime
import numpy as np
from src.down_data_intervals import Intervals, SaveData
from flask import Flask
import threading


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
        self.data = pd.read_csv(f"data/{self.athlete_name}/weekly_stats.csv")
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
        plt.bar(['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Zone 6', 'Zone 7'], [z1_per, z2_per, z3_per, z4_per, z5_per, z6_per, z7_per], color=['red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink'])
        plt.savefig(f"outputs/{self.athlete_name}/email/zones.png", bbox_inches='tight')
        plt.close()

    def send_email(self, info, athlete_name, date, coach_name):

        self.form_chart()
        self.hours_pie_chart()
        self.zones_cumulative_bar_chart()

        # pdf
        athlete_name_unified = athlete_name.replace(" ", "_")
        pdf_output = f"outputs/{athlete_name}/email/{date}.pdf"
        generar_pdf_deportista(pdf_output, athlete_name)

        with open(pdf_output, "rb") as f:
            contenido_pdf = f.read()
        # email
        gmail.user_name = info[coach_name]["email"]
        gmail.password = info[coach_name]["email_pass"]

        for key,values in info.items():
            if values['icu_name'] == athlete_name:
                correo = values['email']
        
        gmail.send(
            subject="Estadísticas semanales de " + athlete_name,
            receivers=[correo],
            html=f"<p>Hola {athlete_name}, adjunto encontrarás tu reporte de rendimiento en PDF.</p>",
            attachments={
                "Reporte_Rendimiento.pdf": contenido_pdf
            }
        )

def ejecutar_proceso_completo():
    try:
        print("Iniciando proceso de datos y envío...")
        # get credentials
        credentials_info = json.load(open("docs/p_info.json"))
        for user, data in credentials_info.items():
            if data['role'] == "coach":
                coach_name = user
        coach_id = credentials_info[coach_name]["id"]
        api_key = credentials_info[coach_name]["password"]

        intervals = Intervals(coach_id, api_key)
        save_data = SaveData(coach_name)

        ########-------------------------------------########
        ########      DOWNLOAD WEEKLY STATS DATA     ########
        ########-------------------------------------########
        # download activities csv
        today_date = datetime.date.today()
        # the sunday of the week before this week
        end_date = today_date - datetime.timedelta(days=today_date.weekday()) - datetime.timedelta(days=1)
        if os.path.exists(f"data/{coach_name}/weekly_stats.csv"):
            old_weekly_stats_df = pd.read_csv(f"data/{coach_name}/weekly_stats.csv")
            start_date = old_weekly_stats_df['date'].max()+ datetime.timedelta(days=1)
        else:
            start_date = end_date - datetime.timedelta(days=30)
            old_weekly_stats_df = pd.DataFrame()
        
        if start_date.date() < end_date:
            weekly_stats_data = intervals.summary_stats(start_date.date(), end_date)
            # list of athletes
            athletes = []
            for athlete, data in credentials_info.items():
                athletes.append(data['icu_name'])
                # save data for every athlete
            for athlete in athletes:
                save_data.weekly_stats_data(weekly_stats_data, athlete, old_weekly_stats_df)


        #---------------------------------------------------#
        #---------------------------------------------------#
        date = datetime.datetime.today() - datetime.timedelta(days=datetime.datetime.today().weekday()) - datetime.timedelta(days=7)
        date_string = date.strftime("%Y-%m-%d")
        for key, values in credentials_info.items():
            if values['role']=='coach':
                coach_name = key
            athlete_name = values['icu_name']
            email_com = WriteEmail(athlete_name, date_string)
            print(f"Sending email to {athlete_name}")
            email_com.send_email(credentials_info, athlete_name, date_string, coach_name)

        print("Proceso finalizado con éxito.")
    except Exception as e:
        print(f"Error: {e}")

@app.route("/")
def home():
    # Lanzamos el proceso en segundo plano para no bloquear la respuesta
    threading.Thread(target=ejecutar_proceso_completo).start()
    return "Servidor activo. Proceso de envío iniciado.", 200

if __name__ == "__main__":
    
    """
    hay que añadir un temporizador para que se ejecute automatico
    todos los domingos a las 21:00
    """
    # Cloud Run inyecta la variable PORT, si no existe usa 8080
    port = int(os.environ.get("PORT", 8080))
    # '0.0.0.0' es obligatorio para que sea accesible
    app.run(host='0.0.0.0', port=port)

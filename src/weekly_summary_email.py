import os
from fpdf import FPDF
from redmail import gmail
import matplotlib.pyplot as plt
import json




class ReporteDeportista(FPDF):

    def __init__(self, athlete_name):
        super().__init__()
        self.athlete_name = athlete_name

    def header(self):
        self.set_font("helvetica", "B", 15)
        self.cell(0, 10, f"Resumen de Rendimiento: {self.athlete_name}", 0, 1, "C")
        self.ln(5)

def generar_pdf_deportista(nombre_archivo):
        pdf = ReporteDeportista()
        pdf.add_page()
        pdf.set_font("helvetica", size=12)

        # Introducción
        pdf.multi_cell(0, 10, "Hola,\nAquí tienes el análisis visual y las estadísticas correspondientes a la última sesión. Los datos muestran un progreso constante.")
        pdf.ln(5)

        # Listado de imágenes a incluir
        graficos = [
            ("1. Intensidad de Entrenamiento", "outputs/email/form.png"),
            ("2. Comparativa Semanal", "outputs/email/hours.png"),
            ("3. Distribución de Zonas", "outputs/email/zones.png")
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
    def __init__(
            self, 
            athlete_name, 
            start_week_date,
            fin_week_date, total_hours,
            total_distance, 
            total_elevation_gain, 
            form, 
            ramp,
            time_zones, 
            run_hours, 
            ride_hours, 
            other_hours
        ):
        self.athlete_name = athlete_name
        self.start_week_date = start_week_date
        self.fin_week_date = fin_week_date
        self.total_hours = total_hours
        self.total_distance = total_distance
        self.form = form
        self.ramp = ramp
        self.total_elevation_gain = total_elevation_gain
        self.time_zones = time_zones
        self.run_hours = run_hours
        self.ride_hours = ride_hours
        self.other_hours = other_hours
    

    def form_chart(self):
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
        ax.bar(1, self.form, color='black', width=0.5)
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
        os.makedirs("outputs/email",exist_ok=True)
        plt.savefig("outputs/email/form.png", bbox_inches='tight')
        plt.close()
    
    def hours_pie_chart(self):
        labels = 'Run', 'Ride', 'Other'
        sizes = [self.run_hours, self.ride_hours, self.other_hours]
        explode = (0, 0, 0.1)
        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                shadow=True, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.savefig("outputs/email/hours.png", bbox_inches='tight')
        plt.close()
    
    def zones_cumulative_bar_chart(self):
        total_time= sum(self.time_zones)
        z1_per= self.time_zones[0]/total_time*100
        z2_per= self.time_zones[1]/total_time*100
        z3_per= self.time_zones[2]/total_time*100
        z4_per= self.time_zones[3]/total_time*100
        z5_per= self.time_zones[4]/total_time*100   
        z6_per= self.time_zones[5]/total_time*100
        z7_per= self.time_zones[6]/total_time*100

        # graph in bars each in a personalizeed color
        plt.figure(figsize=(10, 5))
        plt.bar(['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Zone 6', 'Zone 7'], [z1_per, z2_per, z3_per, z4_per, z5_per, z6_per, z7_per], color=['red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink'])
        plt.savefig("outputs/email/zones.png", bbox_inches='tight')
        plt.close()

    def send_email(self, info, athlete_name):

        self.form_chart()
        self.hours_pie_chart()
        self.zones_cumulative_bar_chart()

        # pdf
        athlete_name_unified = athlete_name.replace(" ", "_")
        pdf_output = f"outputs/email/{athlete_name_unified}.pdf"
        generar_pdf_deportista(pdf_output)

        with open(pdf_output, "rb") as f:
            contenido_pdf = f.read()
        # email
        gmail.user_name = info[athlete_name]["email"]
        gmail.password = info[athlete_name]["email_pass"]
        
        gmail.send(
            subject="Estadísticas semanales de " + athlete_name,
            receivers=[gmail.user_name],
            html=f"<p>Hola {athlete_name}, adjunto encontrarás tu reporte de rendimiento en PDF.</p>",
            attachments={
                "Reporte_Rendimiento.pdf": contenido_pdf
            }
        )

if __name__ == "__main__":
    
    communication_info = json.load("docs/p_info.json")
    for key in communication_info.keys():
        if communication_info[key]["role"] == "coach":
            coach_name = key

            
            athlete_name = key
            print(f"Sending email to {athlete_name}")
            weekly_summary_email = WeeklySummaryEmail(athlete_name)

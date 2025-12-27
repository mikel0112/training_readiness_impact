FROM ubuntu:20.04

# Evita preguntas interactivas durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y python3-pip

# 1. Definir dónde vamos a trabajar dentro del contenedor
WORKDIR /app

# 2. Copiar TODO el contenido de tu repo al contenedor
COPY . .

# 3. Instalar dependencias (ahora que ya se copiaron)
RUN pip3 install -r requirements.txt

# 4. Ejecutar el script (ajusta la ruta si está dentro de src/)

# SI TU ARCHIVO ESTÁ DENTRO DE LA CARPETA SRC, USA ESTA LÍNEA EN SU LUGAR:
CMD ["python3", "src/weekly_summary_email.py"]
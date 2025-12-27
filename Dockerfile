FROM ubuntu:20.04

# Evita que la instalación se detenga pidiendo zona horaria
ENV DEBIAN_FRONTEND=noninteractive

# Instalamos python, pip y herramientas de compilación básicas
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiamos los archivos
COPY . .

# Actualizamos pip e instalamos los requisitos
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

# Ejecutamos el script (ajusta la ruta si está en src/)
CMD ["python3", "src/weekly_summary_email.py"]
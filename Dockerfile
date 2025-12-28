FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/outputs /app/data
RUN chmod -R 777 /app/outputs /app/data
COPY . .
# Esto añade la carpeta actual al PATH de Python
ENV PYTHONPATH="${PYTHONPATH}:/app"
CMD ["python", "src/weekly_summary_email.py"]
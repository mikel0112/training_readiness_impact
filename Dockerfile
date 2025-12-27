FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Esto añade la carpeta actual al PATH de Python
ENV PYTHONPATH="${PYTHONPATH}:/app"
CMD ["python", "src/weekly_summary_email.py"]
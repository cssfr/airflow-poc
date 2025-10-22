FROM apache/airflow:2.8.0-python3.11

# Install system dependencies
USER root
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Copy requirements and install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copy POC-2 code into the image
COPY config/ /opt/airflow/config/
COPY utils/ /opt/airflow/utils/
COPY strategies/ /opt/airflow/strategies/
COPY engines/ /opt/airflow/engines/
# COPY dags/ /opt/airflow/dags/
COPY scripts/ /opt/airflow/scripts/

# Set Python path
# ENV PYTHONPATH="/opt/airflow:${PYTHONPATH}"
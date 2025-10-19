# POC-2 Setup Guide

## Local Development Setup

### 1. Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Access to Supabase instance
- Access to MinIO instance

### 2. Environment Setup

```bash
# Clone or create the project directory
cd poc-2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required environment variables:

```bash
# Supabase Configuration
SUPABASE_URL=http://kong:8000  # or your external Supabase URL
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_ANON_KEY=your_anon_key

# MinIO Configuration
MINIO_ENDPOINT=your-minio-endpoint:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_BUCKET=trading-data
MINIO_USE_SSL=false

# Airflow Configuration
AIRFLOW_POSTGRES_USER=airflow
AIRFLOW_POSTGRES_PASSWORD=airflow_secure_password
AIRFLOW_POSTGRES_DB=airflow
```

### 4. Database Setup

```bash
# Run Alembic migrations to create Supabase tables
alembic upgrade head
```

### 5. Seed Built-in Strategies

```bash
# Insert built-in strategies into Supabase
python scripts/seed_strategies.py
```

### 6. Test Connections

```bash
# Test all connections and components
python scripts/test_connection.py
```

### 7. Start Airflow (Local Development)

```bash
# Start Airflow services
docker-compose up -d

# Check logs
docker-compose logs -f airflow-webserver
```

### 8. Access Airflow UI

- URL: http://localhost:8080
- Username: admin
- Password: admin

## Troubleshooting

### Common Issues

1. **Supabase Connection Failed**
   - Check `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
   - Verify Kong API gateway is accessible
   - Test with: `curl http://kong:8000/health`

2. **MinIO Connection Failed**
   - Check MinIO credentials and endpoint
   - Verify bucket exists and is accessible
   - Test with: `aws s3 ls s3://trading-data --endpoint-url http://your-minio-endpoint:9000`

3. **Strategy Loading Failed**
   - Check strategy code syntax
   - Verify `strategy_class` name matches code
   - Run `python scripts/seed_strategies.py` again

4. **DAG Not Visible**
   - Check Airflow logs for import errors
   - Verify all dependencies are installed
   - Check Python path in Docker containers

### Logs

```bash
# View Airflow logs
docker-compose logs airflow-webserver
docker-compose logs airflow-scheduler
docker-compose logs airflow-worker

# View specific DAG run
docker exec -it poc-2-airflow-webserver-1 airflow tasks log backtest_dag validate_and_create_job 2024-01-01
```

### Reset Everything

```bash
# Stop and remove containers
docker-compose down -v

# Remove volumes
docker volume rm poc-2_postgres_data poc-2_airflow_logs

# Start fresh
docker-compose up -d
```

## Next Steps

1. **Manual Trigger**: See `docs/manual_trigger.md`
2. **Coolify Deployment**: See `docs/coolify_deployment.md`
3. **Strategy Development**: Add your own strategies to Supabase
4. **FastAPI Integration**: Use the same Supabase client in FastAPI


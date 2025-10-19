# POC-2: Airflow Backtesting System

A proof-of-concept Airflow-based backtesting system that integrates with Supabase for strategy storage and MinIO for market data.

## 🏗️ Architecture

- **Airflow**: Orchestrates backtesting workflows
- **Supabase**: Stores strategies, backtest results, and user data
- **MinIO**: Provides OHLCV market data via S3-compatible API
- **PostgreSQL**: Airflow's internal database
- **Redis**: Celery message broker

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Coolify (for deployment)
- Supabase instance
- MinIO instance

### Environment Variables

```bash
# Supabase
SUPABASE_URL=https://your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# MinIO
MINIO_ENDPOINT=your-minio-endpoint:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_BUCKET=trading-data

# Airflow Database
AIRFLOW_POSTGRES_USER=airflow
AIRFLOW_POSTGRES_PASSWORD=airflow_secure_password
AIRFLOW_POSTGRES_DB=airflow
```

### Deployment

1. **Clone this repository**
2. **Set environment variables** in Coolify
3. **Deploy via Coolify** using the `docker-compose.yml`
4. **Access Airflow UI** at your domain
5. **Run seed script** to populate strategies

## 📁 Project Structure

```
poc-2/
├── Dockerfile                 # Airflow image with POC-2 code
├── docker-compose.yml        # Full Airflow stack
├── requirements.txt          # Python dependencies
├── config/                   # Configuration management
├── utils/                    # Supabase client, strategy loader, data manager
├── strategies/               # Base strategy classes
├── engines/                  # Backtesting engines (custom, backtrader, etc.)
├── dags/                     # Airflow DAGs
├── scripts/                  # Utility scripts
└── docs/                     # Documentation
```

## 🔧 Key Features

- **Multi-Engine Support**: Custom, Backtrader, VectorBT engines
- **Strategy Storage**: Code stored in Supabase with RLS
- **Dynamic Loading**: Strategies loaded at runtime
- **Performance Tracking**: Comprehensive backtest metrics
- **Scalable**: Celery executor for distributed processing

## 📚 Documentation

- [Setup Guide](docs/setup.md)
- [Coolify Deployment](docs/coolify_deployment.md)
- [Manual DAG Triggering](docs/manual_trigger.md)

## 🧪 Testing

Use `test_dag.py` to verify your deployment:

```bash
# In Airflow UI, trigger the test_dag
# Or via CLI:
airflow dags trigger test_dag
```

## 🔄 Workflow

1. **Strategy Creation**: Users create strategies in Supabase
2. **DAG Trigger**: FastAPI triggers Airflow DAG with parameters
3. **Data Loading**: OHLCV data fetched from MinIO
4. **Strategy Execution**: Strategy code loaded and executed
5. **Results Storage**: Backtest results saved to Supabase

## 🛠️ Development

### Local Development

```bash
# Build and run locally
docker-compose up --build

# Access Airflow UI
open http://localhost:8080
```

### Adding New Engines

1. Create engine class in `engines/`
2. Implement `BaseEngine` interface
3. Register in `EngineFactory`
4. Update strategy metadata

## 📝 License

Private project - All rights reserved

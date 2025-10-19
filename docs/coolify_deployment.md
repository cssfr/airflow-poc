# Coolify Deployment Guide

## Overview

This guide covers deploying POC-2 on Coolify with self-hosted Supabase and MinIO.

## Prerequisites

- Coolify instance running on Hetzner server
- Self-hosted Supabase stack deployed
- MinIO instance accessible
- Docker and Docker Compose knowledge

## Architecture

```
Coolify (Hetzner Server)
├── Supabase Stack (existing)
│   ├── Kong API Gateway (http://kong:8000)
│   ├── PostgreSQL
│   └── Other services
└── Airflow Stack (new POC-2)
    ├── Airflow Webserver
    ├── Airflow Scheduler
    ├── Airflow Worker
    ├── Redis
    └── PostgreSQL (Airflow metadata)
```

## Deployment Steps

### 1. Create New Service Stack

1. Log into Coolify
2. Navigate to your project
3. Click "New Service Stack"
4. Choose "Docker Compose"

### 2. Upload Configuration

Upload the `docker-compose.yml` file from the POC-2 project.

### 3. Configure Environment Variables

Set the following environment variables in Coolify:

```bash
# Supabase Configuration
SUPABASE_URL=http://kong:8000
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_from_supabase
SUPABASE_ANON_KEY=your_anon_key_from_supabase

# MinIO Configuration
MINIO_ENDPOINT=your-minio-endpoint:9000
MINIO_ACCESS_KEY=your_minio_access_key
MINIO_SECRET_KEY=your_minio_secret_key
MINIO_BUCKET=trading-data
MINIO_USE_SSL=false

# Airflow Configuration
AIRFLOW_POSTGRES_USER=airflow
AIRFLOW_POSTGRES_PASSWORD=airflow_secure_password_123
AIRFLOW_POSTGRES_DB=airflow
```

### 4. Network Configuration

1. **Connect to Supabase Network**: Ensure the Airflow stack can communicate with Supabase
2. **Internal URLs**: Use `http://kong:8000` for Supabase API calls
3. **External Access**: Configure port 8080 for Airflow UI access

### 5. Deploy Stack

1. Click "Deploy" in Coolify
2. Monitor the deployment logs
3. Wait for all services to be healthy

### 6. Post-Deployment Setup

#### 6.1 Run Database Migrations

```bash
# Connect to the airflow-webserver container
docker exec -it <airflow-webserver-container> bash

# Run Alembic migrations
alembic upgrade head
```

#### 6.2 Seed Built-in Strategies

```bash
# In the same container
python scripts/seed_strategies.py
```

#### 6.3 Test Connections

```bash
# Test all connections
python scripts/test_connection.py
```

### 7. Access Airflow UI

- **Internal URL**: `http://airflow-webserver:8080` (from within Coolify network)
- **External URL**: Configure in Coolify for external access
- **Credentials**: admin / admin

## Environment Variables Mapping

### From Coolify Supabase Environment

Map these Supabase environment variables to POC-2:

```bash
# Coolify Supabase → POC-2
SERVICE_SUPABASESERVICE_KEY → SUPABASE_SERVICE_ROLE_KEY
SERVICE_SUPABASEANON_KEY → SUPABASE_ANON_KEY
```

### Supabase URL Configuration

- **Internal**: `http://kong:8000` (within Coolify network)
- **External**: `https://supa-stage.backtesting.theworkpc.com` (if needed)

## Network Configuration

### Internal Communication

- Airflow → Supabase: `http://kong:8000`
- Airflow → MinIO: Direct S3-compatible connection
- Airflow → Redis: `redis://redis:6379`
- Airflow → PostgreSQL: `postgresql://postgres:5432`

### External Access

- Airflow UI: Port 8080 (configure in Coolify)
- Supabase API: Port 8000 (Kong gateway)
- MinIO: Port 9000 (if external access needed)

## Monitoring and Logs

### View Logs in Coolify

1. Navigate to your Airflow service stack
2. Click on individual services to view logs
3. Monitor for errors and warnings

### Common Log Locations

- **Airflow Webserver**: `/opt/airflow/logs/`
- **Airflow Scheduler**: `/opt/airflow/logs/`
- **Airflow Worker**: `/opt/airflow/logs/`

### Health Checks

```bash
# Check Airflow webserver
curl http://airflow-webserver:8080/health

# Check Supabase connection
curl http://kong:8000/health

# Check MinIO connection
aws s3 ls s3://trading-data --endpoint-url http://minio:9000
```

## Troubleshooting

### Common Issues

1. **Container Startup Failures**
   - Check environment variables
   - Verify network connectivity
   - Check resource limits

2. **Supabase Connection Issues**
   - Verify `SUPABASE_URL` is correct
   - Check service role key permissions
   - Test Kong API gateway accessibility

3. **MinIO Connection Issues**
   - Verify MinIO credentials
   - Check network connectivity
   - Verify bucket exists

4. **DAG Import Errors**
   - Check Python dependencies
   - Verify file permissions
   - Check import paths

### Debug Commands

```bash
# Check container status
docker ps

# View container logs
docker logs <container-name>

# Execute commands in container
docker exec -it <container-name> bash

# Check network connectivity
docker exec -it <container-name> ping kong
docker exec -it <container-name> ping minio
```

## Scaling and Performance

### Resource Requirements

- **Minimum**: 2 CPU cores, 4GB RAM
- **Recommended**: 4 CPU cores, 8GB RAM
- **Storage**: 20GB for Airflow metadata, logs, and data

### Scaling Options

1. **Horizontal Scaling**: Add more Airflow workers
2. **Vertical Scaling**: Increase CPU/memory limits
3. **Storage Scaling**: Add persistent volumes for logs

### Performance Optimization

1. **Redis Configuration**: Tune Redis for better performance
2. **PostgreSQL Tuning**: Optimize Airflow metadata database
3. **Worker Configuration**: Adjust worker concurrency

## Security Considerations

1. **Network Security**: Use internal networks for service communication
2. **Authentication**: Change default Airflow admin password
3. **Secrets Management**: Use Coolify's secret management for sensitive data
4. **Access Control**: Limit external access to necessary ports only

## Backup and Recovery

### Database Backups

```bash
# Backup Airflow metadata database
docker exec <postgres-container> pg_dump -U airflow airflow > airflow_backup.sql

# Backup Supabase data (handled by Supabase stack)
```

### Configuration Backups

- Save environment variables
- Backup docker-compose.yml
- Document custom configurations

## Maintenance

### Regular Tasks

1. **Log Rotation**: Configure log rotation for Airflow logs
2. **Database Cleanup**: Clean old DAG run data
3. **Security Updates**: Keep Docker images updated
4. **Monitoring**: Set up alerts for service failures

### Updates

1. **Code Updates**: Deploy new versions through Coolify
2. **Dependency Updates**: Update requirements.txt and redeploy
3. **Configuration Changes**: Update environment variables in Coolify


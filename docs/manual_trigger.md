# Manual Trigger Guide

## Overview

This guide shows how to manually trigger the `backtest_dag` with different configurations.

## Basic Trigger Command

```bash
docker exec -it <airflow-webserver-container> airflow dags trigger backtest_dag --conf '{
    "job_id": "job_12345",
    "user_id": "user_uuid",
    "strategy_id": "strategy_uuid",
    "symbol": "DJIA",
    "timeframe": "15m",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "parameters": {}
}'
```

## Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `job_id` | string | Unique job identifier | `"job_12345"` |
| `user_id` | string | User UUID | `"550e8400-e29b-41d4-a716-446655440000"` |
| `strategy_id` | string | Strategy UUID from Supabase | `"550e8400-e29b-41d4-a716-446655440001"` |
| `symbol` | string | Trading symbol | `"DJIA"`, `"DAX"`, `"ES"` |
| `timeframe` | string | Data timeframe | `"1m"`, `"15m"`, `"1h"` |
| `start_date` | string | Backtest start date (YYYY-MM-DD) | `"2024-01-01"` |
| `end_date` | string | Backtest end date (YYYY-MM-DD) | `"2024-01-31"` |

## Optional Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `initial_capital` | number | Starting capital | `100000` |
| `parameters` | object | Strategy-specific parameters | `{}` |

## Example Configurations

### 1. DAX London Bracket Strategy

```bash
docker exec -it <container> airflow dags trigger backtest_dag --conf '{
    "job_id": "dax_london_001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "strategy_id": "dax_strategy_uuid",
    "symbol": "DAX",
    "timeframe": "15m",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "initial_capital": 100000,
    "parameters": {
        "points_per_trade": 1.0,
        "take_profit_points": 40.0,
        "min_bracket_range": 10.0,
        "fees_per_trade": 0.0
    }
}'
```

### 2. Simple ORB Strategy

```bash
docker exec -it <container> airflow dags trigger backtest_dag --conf '{
    "job_id": "orb_strategy_001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "strategy_id": "orb_strategy_uuid",
    "symbol": "ES",
    "timeframe": "15m",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "initial_capital": 50000,
    "parameters": {
        "orb_minutes": 15,
        "stop_loss_pct": 0.02,
        "take_profit_pct": 0.04
    }
}'
```

### 3. Multiple Symbols Test

```bash
# DJIA Test
docker exec -it <container> airflow dags trigger backtest_dag --conf '{
    "job_id": "djia_test_001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "strategy_id": "orb_strategy_uuid",
    "symbol": "DJIA",
    "timeframe": "1m",
    "start_date": "2024-01-01",
    "end_date": "2024-01-07",
    "parameters": {
        "orb_minutes": 15,
        "stop_loss_pct": 0.01,
        "take_profit_pct": 0.02
    }
}'

# ES Test
docker exec -it <container> airflow dags trigger backtest_dag --conf '{
    "job_id": "es_test_001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "strategy_id": "orb_strategy_uuid",
    "symbol": "ES",
    "timeframe": "1m",
    "start_date": "2024-01-01",
    "end_date": "2024-01-07",
    "parameters": {
        "orb_minutes": 15,
        "stop_loss_pct": 0.01,
        "take_profit_pct": 0.02
    }
}'
```

## Getting Strategy IDs

### 1. List Available Strategies

```bash
# Connect to Supabase and query strategies
docker exec -it <container> python -c "
from utils.supabase_client import supabase_client
result = supabase_client.client.table('strategies').select('id, name, is_public').execute()
for strategy in result.data:
    print(f'ID: {strategy[\"id\"]}, Name: {strategy[\"name\"]}, Public: {strategy[\"is_public\"]}')
"
```

### 2. Get Specific Strategy

```bash
# Get DAX strategy ID
docker exec -it <container> python -c "
from utils.supabase_client import supabase_client
result = supabase_client.client.table('strategies').select('id').eq('name', 'DAX London Bracket Strategy').execute()
if result.data:
    print(f'DAX Strategy ID: {result.data[0][\"id\"]}')
else:
    print('DAX strategy not found')
"
```

## Monitoring DAG Runs

### 1. Check DAG Status

```bash
# List recent DAG runs
docker exec -it <container> airflow dags list-runs -d backtest_dag --limit 10
```

### 2. View Task Logs

```bash
# View logs for specific task
docker exec -it <container> airflow tasks log backtest_dag validate_and_create_job <execution-date>
```

### 3. Check Backtest Results

```bash
# Query backtest results from Supabase
docker exec -it <container> python -c "
from utils.supabase_client import supabase_client
result = supabase_client.client.table('backtests').select('*').eq('job_id', 'job_12345').execute()
if result.data:
    backtest = result.data[0]
    print(f'Status: {backtest[\"status\"]}')
    print(f'Total Trades: {backtest[\"total_trades\"]}')
    print(f'Final Value: {backtest[\"final_value\"]}')
    print(f'Total Return: {backtest[\"total_return\"]}')
else:
    print('Backtest not found')
"
```

## Error Handling

### Common Errors

1. **Missing Strategy**
   ```
   ValueError: Strategy <uuid> not found
   ```
   - Solution: Check strategy ID exists in Supabase

2. **Invalid Date Format**
   ```
   ValueError: Invalid date format
   ```
   - Solution: Use YYYY-MM-DD format for dates

3. **Symbol Not Available**
   ```
   ValueError: Symbol not available in data
   ```
   - Solution: Check symbol exists in MinIO data

4. **Connection Failed**
   ```
   ConnectionError: Failed to connect to Supabase
   ```
   - Solution: Check Supabase URL and credentials

### Debug Mode

```bash
# Enable debug logging
docker exec -it <container> airflow config set-value logging logging_level DEBUG

# View detailed logs
docker exec -it <container> airflow tasks log backtest_dag validate_and_create_job <execution-date> --full
```

## Batch Testing

### Test Multiple Configurations

Create a test script:

```bash
#!/bin/bash
# test_batch.sh

STRATEGIES=("dax_strategy_uuid" "orb_strategy_uuid")
SYMBOLS=("DJIA" "DAX" "ES")
USER_ID="550e8400-e29b-41d4-a716-446655440000"

for strategy in "${STRATEGIES[@]}"; do
    for symbol in "${SYMBOLS[@]}"; do
        job_id="test_${strategy}_${symbol}_$(date +%s)"
        
        docker exec -it <container> airflow dags trigger backtest_dag --conf "{
            \"job_id\": \"$job_id\",
            \"user_id\": \"$USER_ID\",
            \"strategy_id\": \"$strategy\",
            \"symbol\": \"$symbol\",
            \"timeframe\": \"15m\",
            \"start_date\": \"2024-01-01\",
            \"end_date\": \"2024-01-07\",
            \"parameters\": {}
        }"
        
        echo "Triggered job: $job_id"
        sleep 5  # Wait between triggers
    done
done
```

## Performance Testing

### Large Dataset Test

```bash
# Test with 1 month of 1-minute data
docker exec -it <container> airflow dags trigger backtest_dag --conf '{
    "job_id": "perf_test_001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "strategy_id": "orb_strategy_uuid",
    "symbol": "DJIA",
    "timeframe": "1m",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "parameters": {
        "orb_minutes": 15,
        "stop_loss_pct": 0.02,
        "take_profit_pct": 0.04
    }
}'
```

### Memory Usage Monitoring

```bash
# Monitor container memory usage
docker stats <airflow-worker-container>

# Check Airflow worker memory
docker exec -it <container> airflow config get-value celery worker_memory_limit
```

## Best Practices

1. **Unique Job IDs**: Always use unique job IDs to avoid conflicts
2. **Reasonable Date Ranges**: Start with small date ranges for testing
3. **Monitor Resources**: Watch CPU and memory usage during backtests
4. **Check Logs**: Always check logs for errors and warnings
5. **Validate Results**: Verify backtest results in Supabase
6. **Clean Up**: Remove old test data periodically

## Troubleshooting

### DAG Not Triggering

1. Check DAG is visible in Airflow UI
2. Verify all required parameters are provided
3. Check for syntax errors in JSON configuration
4. Verify container is running and accessible

### Tasks Failing

1. Check task logs for specific error messages
2. Verify Supabase and MinIO connections
3. Check strategy code syntax
4. Verify data availability for the specified date range

### Performance Issues

1. Monitor container resource usage
2. Check database connection limits
3. Verify MinIO performance
4. Consider reducing date range or timeframe


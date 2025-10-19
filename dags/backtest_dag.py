from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import logging
import json
from typing import Dict, Any

# Import our custom modules
from utils.supabase_client import supabase_client
from utils.strategy_loader import strategy_loader
from utils.data_manager import data_manager
from engines.engine_factory import EngineFactory

logger = logging.getLogger(__name__)

# Default arguments for the DAG
default_args = {
    'owner': 'poc-2',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'backtest_dag',
    default_args=default_args,
    description='POC-2 Backtest DAG - Complete backtesting workflow',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['poc-2', 'backtest'],
)


def validate_and_create_job(**context) -> Dict[str, Any]:
    """
    Task 1: Validate trigger configuration and create backtest job
    """
    try:
        # Get configuration from trigger
        dag_run = context['dag_run']
        conf = dag_run.conf or {}
        
        # Validate required parameters
        required_params = ['job_id', 'user_id', 'strategy_id', 'symbol', 'timeframe', 'start_date', 'end_date']
        missing_params = [param for param in required_params if param not in conf]
        
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
        
        # Validate dates
        start_date = datetime.strptime(conf['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(conf['end_date'], '%Y-%m-%d').date()
        
        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")
        
        # Create backtest record in Supabase (matching your schema)
        job_data = {
            'job_id': conf['job_id'],
            'user_id': conf['user_id'],
            'strategy_id': conf['strategy_id'],
            'name': f"Backtest {conf['symbol']} {conf['timeframe']}",
            'strategy': conf['strategy_id'],  # Your schema uses 'strategy' instead of 'strategy_id'
            'symbol': conf['symbol'],
            'timeframe': conf['timeframe'],
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'initial_capital': conf.get('initial_capital', 10000),
            'status': 'running'
        }
        
        # Create the backtest record
        backtest_record = supabase_client.create_backtest(job_data)
        
        logger.info(f"Created backtest job: {conf['job_id']}")
        
        # Return configuration for next tasks
        return {
            'job_id': conf['job_id'],
            'user_id': conf['user_id'],
            'strategy_id': conf['strategy_id'],
            'symbol': conf['symbol'],
            'timeframe': conf['timeframe'],
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': conf.get('initial_capital', 10000),
            'parameters': conf.get('parameters', {}),
            'backtest_id': backtest_record['id']
        }
        
    except Exception as e:
        logger.error(f"Error in validate_and_create_job: {e}")
        # Update status to failed
        if 'job_id' in conf:
            supabase_client.update_backtest(conf['job_id'], {'status': 'failed'})
        raise


def load_strategy(**context) -> Dict[str, Any]:
    """
    Task 2: Load strategy from Supabase
    """
    try:
        # Get configuration from previous task
        config = context['task_instance'].xcom_pull(task_ids='validate_and_create_job')
        
        # Load strategy from Supabase
        strategy_class = strategy_loader.load_strategy(config['strategy_id'])
        
        logger.info(f"Loaded strategy: {strategy_class.__name__}")
        
        # Return strategy info
        return {
            'strategy_class': strategy_class.__name__,
            'strategy_loaded': True
        }
        
    except Exception as e:
        logger.error(f"Error in load_strategy: {e}")
        # Update status to failed
        supabase_client.update_backtest(config['job_id'], {'status': 'failed'})
        raise


def fetch_data(**context) -> Dict[str, Any]:
    """
    Task 3: Fetch OHLCV data from MinIO
    """
    try:
        # Get configuration from previous task
        config = context['task_instance'].xcom_pull(task_ids='validate_and_create_job')
        
        # Fetch data from MinIO
        data = data_manager.get_ohlcv_data(
            symbol=config['symbol'],
            timeframe=config['timeframe'],
            start_date=config['start_date'],
            end_date=config['end_date']
        )
        
        logger.info(f"Fetched {len(data)} rows of data for {config['symbol']} {config['timeframe']}")
        
        # Store data reference (in production, you might want to store in temp file or S3)
        # For now, we'll pass the data info
        return {
            'data_rows': len(data),
            'data_columns': list(data.columns),
            'data_start': data['timestamp'][0].isoformat() if len(data) > 0 else None,
            'data_end': data['timestamp'][-1].isoformat() if len(data) > 0 else None,
            'data_available': len(data) > 0
        }
        
    except Exception as e:
        logger.error(f"Error in fetch_data: {e}")
        # Update status to failed
        supabase_client.update_backtest(config['job_id'], {'status': 'failed'})
        raise


def execute_backtest(**context) -> Dict[str, Any]:
    """
    Task 4: Execute the backtest
    """
    try:
        # Get configuration and data info
        config = context['task_instance'].xcom_pull(task_ids='validate_and_create_job')
        data_info = context['task_instance'].xcom_pull(task_ids='fetch_data')
        
        if not data_info['data_available']:
            raise ValueError("No data available for backtest")
        
        # Fetch data again (in production, you'd retrieve from storage)
        data = data_manager.get_ohlcv_data(
            symbol=config['symbol'],
            timeframe=config['timeframe'],
            start_date=config['start_date'],
            end_date=config['end_date']
        )
        
        # Load strategy
        strategy_class = strategy_loader.load_strategy(config['strategy_id'])
        
        # Get strategy metadata to determine engine type
        strategy_metadata = supabase_client.get_strategy(config['strategy_id'])
        engine_type = strategy_metadata.get('engine_type', 'custom')
        engine_config = strategy_metadata.get('engine_config', {})
        
        # Add backtest config to engine config
        engine_config.update({
            'initial_capital': config['initial_capital'],
            'start_date': config['start_date'],
            'end_date': config['end_date']
        })
        
        # Create the appropriate engine using factory
        engine = EngineFactory.create_engine(engine_type, engine_config)
        
        # Validate strategy compatibility
        if not engine.validate_strategy(strategy_class):
            raise ValueError(f"Strategy {config['strategy_id']} is not compatible with engine {engine_type}")
        
        # Run the backtest
        results = engine.run_backtest(data, strategy_class, config)
        
        logger.info(f"Backtest completed: {results['trades_count']} trades, {results['performance_metrics']['total_return_pct']:.2f}% return")
        
        # Return results
        return {
            'trades_count': results['trades_count'],
            'performance_metrics': results['performance_metrics'],
            'engine_info': results['engine_info'],
            'trades': [
                {
                    'symbol': trade.symbol,
                    'trade_type': trade.trade_type.value,
                    'quantity': float(trade.quantity),
                    'price': float(trade.price),
                    'timestamp': trade.timestamp.isoformat(),
                    'pnl': float(trade.pnl),
                    'fees': float(trade.fees)
                }
                for trade in results['trades']
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in execute_backtest: {e}")
        # Update status to failed
        supabase_client.update_backtest(config['job_id'], {'status': 'failed'})
        raise


def save_results(**context) -> Dict[str, Any]:
    """
    Task 5: Save results to Supabase
    """
    try:
        # Get configuration and results
        config = context['task_instance'].xcom_pull(task_ids='validate_and_create_job')
        results = context['task_instance'].xcom_pull(task_ids='execute_backtest')
        
        # Save trades to Supabase
        if results['trades']:
            trades_data = []
            for trade in results['trades']:
                trades_data.append({
                    'backtest_id': config['backtest_id'],
                    'trade_type': trade['trade_type'],
                    'symbol': trade['symbol'],
                    'quantity': trade['quantity'],
                    'price': trade['price'],
                    'timestamp': trade['timestamp']
                })
            
            supabase_client.save_trades(trades_data)
        
        # Update backtest with performance metrics (matching your schema)
        metrics = results['performance_metrics']
        update_data = {
            'status': 'completed',
            'final_value': config['initial_capital'] * (1 + metrics['total_return']),
            'total_return': metrics['total_return'],
            'max_drawdown': metrics['max_drawdown'],
            'sharpe_ratio': metrics['sharpe_ratio'],
            'win_rate': metrics['win_rate'],
            'total_trades': metrics['total_trades']
        }
        
        supabase_client.update_backtest(config['job_id'], update_data)
        
        logger.info(f"Saved results for backtest: {config['job_id']}")
        
        return {
            'status': 'completed',
            'trades_saved': len(results['trades']),
            'metrics_saved': True
        }
        
    except Exception as e:
        logger.error(f"Error in save_results: {e}")
        # Update status to failed
        supabase_client.update_backtest(config['job_id'], {'status': 'failed'})
        raise


# Define tasks
validate_task = PythonOperator(
    task_id='validate_and_create_job',
    python_callable=validate_and_create_job,
    dag=dag,
)

load_strategy_task = PythonOperator(
    task_id='load_strategy',
    python_callable=load_strategy,
    dag=dag,
)

fetch_data_task = PythonOperator(
    task_id='fetch_data',
    python_callable=fetch_data,
    dag=dag,
)

execute_backtest_task = PythonOperator(
    task_id='execute_backtest',
    python_callable=execute_backtest,
    dag=dag,
)

save_results_task = PythonOperator(
    task_id='save_results',
    python_callable=save_results,
    dag=dag,
)

# Define task dependencies
validate_task >> load_strategy_task >> fetch_data_task >> execute_backtest_task >> save_results_task
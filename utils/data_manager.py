import duckdb
import polars as pl
import logging
from typing import Optional, List
from datetime import datetime, date
from config.settings import settings

logger = logging.getLogger(__name__)


class DataManager:
    def __init__(self):
        """Initialize DuckDB connection with MinIO configuration"""
        self.conn = duckdb.connect(':memory:')
        self._setup_minio_connection()
        logger.info(f"Initialized DataManager for MinIO: {settings.MINIO_ENDPOINT}")
    
    def _setup_minio_connection(self) -> None:
        """Configure DuckDB for MinIO S3 access"""
        try:
            # Install and load httpfs extension
            self.conn.execute("INSTALL httpfs")
            self.conn.execute("LOAD httpfs")
            
            # Configure S3 settings for MinIO
            self.conn.execute(f"SET s3_endpoint='{settings.MINIO_ENDPOINT}'")
            self.conn.execute(f"SET s3_access_key_id='{settings.MINIO_ACCESS_KEY}'")
            self.conn.execute(f"SET s3_secret_access_key='{settings.MINIO_SECRET_KEY}'")
            self.conn.execute("SET s3_use_ssl=true")  # Force HTTPS for MinIO
            self.conn.execute("SET s3_url_style='path'")  # MinIO uses path-style URLs
            self.conn.execute("SET s3_region='us-east-1'")  # MinIO default region
            
            logger.info("MinIO connection configured successfully")
            
        except Exception as e:
            logger.error(f"Error setting up MinIO connection: {e}")
            raise
    
    def get_ohlcv_data(
        self, 
        symbol: str, 
        timeframe: str, 
        start_date: date, 
        end_date: date
    ) -> pl.DataFrame:
        """
        Fetch OHLCV data from MinIO for a given symbol and date range
        
        Args:
            symbol: Trading symbol (e.g., 'DJIA', 'BTC')
            timeframe: Timeframe (e.g., '15m', '1h', '1d')
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            Polars DataFrame with OHLCV data
        """
        try:
            # Construct S3 path pattern
            s3_path = f"s3://{settings.MINIO_BUCKET}/{symbol}/{timeframe}/*.parquet"
            
            # Build SQL query
            query = f"""
            SELECT 
                timestamp,
                open,
                high,
                low,
                close,
                volume
            FROM read_parquet('{s3_path}')
            WHERE timestamp >= '{start_date}' 
              AND timestamp <= '{end_date}'
            ORDER BY timestamp
            """
            
            logger.info(f"Fetching data for {symbol} {timeframe} from {start_date} to {end_date}")
            
            # Execute query and convert to Polars
            result = self.conn.execute(query).fetchdf()
            df = pl.from_pandas(result)
            
            logger.info(f"Retrieved {len(df)} rows of data")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV data for {symbol}: {e}")
            raise
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols in MinIO"""
        try:
            # List all symbols (directories in bucket)
            query = f"""
            SELECT DISTINCT 
                regexp_extract(name, '{settings.MINIO_BUCKET}/([^/]+)/', 1) as symbol
            FROM glob('s3://{settings.MINIO_BUCKET}/*/*.parquet')
            WHERE symbol IS NOT NULL
            ORDER BY symbol
            """
            
            result = self.conn.execute(query).fetchdf()
            symbols = result['symbol'].tolist()
            
            logger.info(f"Found {len(symbols)} available symbols: {symbols}")
            return symbols
            
        except Exception as e:
            logger.error(f"Error fetching available symbols: {e}")
            return []
    
    def get_available_timeframes(self, symbol: str) -> List[str]:
        """Get list of available timeframes for a symbol"""
        try:
            query = f"""
            SELECT DISTINCT 
                regexp_extract(name, '{settings.MINIO_BUCKET}/{symbol}/([^/]+)/', 1) as timeframe
            FROM glob('s3://{settings.MINIO_BUCKET}/{symbol}/*/*.parquet')
            WHERE timeframe IS NOT NULL
            ORDER BY timeframe
            """
            
            result = self.conn.execute(query).fetchdf()
            timeframes = result['timeframe'].tolist()
            
            logger.info(f"Found {len(timeframes)} timeframes for {symbol}: {timeframes}")
            return timeframes
            
        except Exception as e:
            logger.error(f"Error fetching timeframes for {symbol}: {e}")
            return []
    
    def get_data_info(self, symbol: str, timeframe: str) -> dict:
        """Get information about available data for a symbol/timeframe"""
        try:
            s3_path = f"s3://{settings.MINIO_BUCKET}/{symbol}/{timeframe}/*.parquet"
            
            query = f"""
            SELECT 
                MIN(timestamp) as earliest_date,
                MAX(timestamp) as latest_date,
                COUNT(*) as total_rows
            FROM read_parquet('{s3_path}')
            """
            
            result = self.conn.execute(query).fetchdf()
            
            if len(result) > 0:
                info = {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'earliest_date': result.iloc[0]['earliest_date'],
                    'latest_date': result.iloc[0]['latest_date'],
                    'total_rows': result.iloc[0]['total_rows']
                }
                logger.info(f"Data info for {symbol} {timeframe}: {info}")
                return info
            else:
                logger.warning(f"No data found for {symbol} {timeframe}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting data info for {symbol} {timeframe}: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test MinIO connection"""
        try:
            # Try to list files in the bucket
            query = f"SELECT COUNT(*) as file_count FROM glob('s3://{settings.MINIO_BUCKET}/*/*.parquet')"
            result = self.conn.execute(query).fetchdf()
            file_count = result.iloc[0]['file_count']
            
            logger.info(f"MinIO connection test successful. Found {file_count} parquet files")
            return True
            
        except Exception as e:
            logger.error(f"MinIO connection test failed: {e}")
            return False
    
    def close(self) -> None:
        """Close DuckDB connection"""
        if self.conn:
            self.conn.close()
            logger.info("DataManager connection closed")


# Global data manager instance
data_manager = DataManager()
from supabase import create_client, Client
from config.settings import settings
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SupabaseClient:
    def __init__(self):
        """Initialize Supabase client with service role key"""
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        logger.info(f"Initialized Supabase client for {settings.SUPABASE_URL}")
    
    def get_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Get strategy with code from Supabase"""
        try:
            result = self.client.table('strategies').select('*').eq('id', strategy_id).execute()
            if not result.data:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            strategy = result.data[0]
            
            # Validate that strategy has required POC-2 fields
            if not strategy.get('code_content'):
                raise ValueError(f"Strategy {strategy_id} missing code_content")
            if not strategy.get('strategy_class'):
                raise ValueError(f"Strategy {strategy_id} missing strategy_class")
            
            return strategy
        except Exception as e:
            logger.error(f"Error fetching strategy {strategy_id}: {e}")
            raise
    
    def get_public_strategies(self) -> List[Dict[str, Any]]:
        """Get all public strategies with POC-2 required fields"""
        try:
            result = self.client.table('strategies').select('*').eq('is_public', True).execute()
            
            # Filter strategies that have POC-2 required fields
            poc2_strategies = []
            for strategy in result.data:
                if strategy.get('code_content') and strategy.get('strategy_class'):
                    poc2_strategies.append(strategy)
                else:
                    logger.warning(f"Strategy {strategy.get('name', 'Unknown')} missing POC-2 fields")
            
            return poc2_strategies
        except Exception as e:
            logger.error(f"Error fetching public strategies: {e}")
            raise
    
    def create_backtest(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create backtest record"""
        try:
            result = self.client.table('backtests').insert(job_data).execute()
            if not result.data:
                raise ValueError("Failed to create backtest record")
            return result.data[0]
        except Exception as e:
            logger.error(f"Error creating backtest: {e}")
            raise
    
    def update_backtest(self, job_id: str, update_data: Dict[str, Any]) -> None:
        """Update backtest record"""
        try:
            result = self.client.table('backtests').update(update_data).eq('job_id', job_id).execute()
            if not result.data:
                logger.warning(f"No backtest found with job_id: {job_id}")
        except Exception as e:
            logger.error(f"Error updating backtest {job_id}: {e}")
            raise
    
    def get_backtest(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get backtest by job_id"""
        try:
            result = self.client.table('backtests').select('*').eq('job_id', job_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching backtest {job_id}: {e}")
            raise
    
    def save_trades(self, trades: List[Dict[str, Any]]) -> None:
        """Bulk insert trades"""
        if not trades:
            logger.info("No trades to save")
            return
        
        try:
            result = self.client.table('trades').insert(trades).execute()
            logger.info(f"Saved {len(trades)} trades")
        except Exception as e:
            logger.error(f"Error saving trades: {e}")
            raise
    
    def get_trades(self, backtest_id: str) -> List[Dict[str, Any]]:
        """Get all trades for a backtest"""
        try:
            result = self.client.table('trades').select('*').eq('backtest_id', backtest_id).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching trades for backtest {backtest_id}: {e}")
            raise
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        try:
            result = self.client.table('users').insert(user_data).execute()
            if not result.data:
                raise ValueError("Failed to create user")
            return result.data[0]
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            result = self.client.table('users').select('*').eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            # Try to fetch a simple query
            result = self.client.table('users').select('id').limit(1).execute()
            logger.info("Supabase connection test successful")
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False


# Global client instance
supabase_client = SupabaseClient()
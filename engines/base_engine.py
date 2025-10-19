from abc import ABC, abstractmethod
from typing import Dict, Any, List
import polars as pl
from datetime import datetime, date


class BaseEngine(ABC):
    """
    Abstract base class for all backtesting engines.
    
    All backtesting engines must implement these methods to ensure
    consistent interface across different libraries (custom, backtrader, vectorbt, etc.)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the engine with configuration
        
        Args:
            config: Engine-specific configuration
        """
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    def run_backtest(
        self, 
        data: pl.DataFrame, 
        strategy: Any, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a backtest using this engine
        
        Args:
            data: OHLCV data as Polars DataFrame
            strategy: Strategy instance or configuration
            config: Backtest configuration (symbol, timeframe, dates, etc.)
            
        Returns:
            Dictionary with backtest results including:
            - trades: List of executed trades
            - performance_metrics: Performance statistics
            - engine_info: Engine-specific information
        """
        pass
    
    @abstractmethod
    def get_required_dependencies(self) -> List[str]:
        """
        Return list of required Python packages for this engine
        
        Returns:
            List of package names (e.g., ['backtrader', 'numpy'])
        """
        pass
    
    @abstractmethod
    def validate_strategy(self, strategy: Any) -> bool:
        """
        Validate that the strategy is compatible with this engine
        
        Args:
            strategy: Strategy instance or configuration
            
        Returns:
            True if strategy is compatible, False otherwise
        """
        pass
    
    @abstractmethod
    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about this engine
        
        Returns:
            Dictionary with engine information (name, version, capabilities, etc.)
        """
        pass
    
    def validate_data(self, data: pl.DataFrame) -> bool:
        """
        Validate that data has required columns for backtesting
        
        Args:
            data: OHLCV data
            
        Returns:
            True if data is valid, False otherwise
        """
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        
        for col in required_columns:
            if col not in data.columns:
                return False
        
        if len(data) == 0:
            return False
        
        return True
    
    def get_data_info(self, data: pl.DataFrame) -> Dict[str, Any]:
        """
        Get information about the data
        
        Args:
            data: OHLCV data
            
        Returns:
            Dictionary with data information
        """
        if len(data) == 0:
            return {}
        
        return {
            'rows': len(data),
            'columns': list(data.columns),
            'start_date': data['timestamp'][0].isoformat() if len(data) > 0 else None,
            'end_date': data['timestamp'][-1].isoformat() if len(data) > 0 else None,
            'symbols': list(data['symbol'].unique()) if 'symbol' in data.columns else ['unknown']
        }
    
    def __str__(self) -> str:
        return f"{self.name}(config={self.config})"
    
    def __repr__(self) -> str:
        return self.__str__()

from typing import Dict, Any, List
import polars as pl
from datetime import datetime, date
import logging

from engines.base_engine import BaseEngine
from engines.custom.signal_engine import SignalEngine
from engines.custom.trade_engine import TradeEngine
from engines.custom.performance_calculator import PerformanceCalculator

logger = logging.getLogger(__name__)


class CustomEngine(BaseEngine):
    """
    Custom backtesting engine using our own signal, trade, and performance engines.
    
    This engine implements the BaseEngine interface and orchestrates
    the custom backtesting workflow.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Initialize sub-engines
        self.signal_engine = SignalEngine()
        self.trade_engine = TradeEngine(
            initial_capital=config.get('initial_capital', 10000),
            commission_rate=config.get('commission_rate', 0.001)
        )
        self.performance_calculator = PerformanceCalculator()
        
        logger.info(f"Initialized CustomEngine with capital: {config.get('initial_capital', 10000)}")
    
    def run_backtest(
        self, 
        data: pl.DataFrame, 
        strategy: Any, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a backtest using the custom engine
        
        Args:
            data: OHLCV data as Polars DataFrame
            strategy: Strategy instance
            config: Backtest configuration
            
        Returns:
            Dictionary with backtest results
        """
        try:
            # Validate data
            if not self.validate_data(data):
                raise ValueError("Invalid data for backtesting")
            
            logger.info(f"Starting backtest with {len(data)} data points")
            
            # Generate signals
            signals = self.signal_engine.generate_signals(strategy, data)
            logger.info(f"Generated {len(signals)} signals")
            
            # Execute trades
            trades = []
            for signal in signals:
                # Get current price (simplified - in production you'd get from data)
                current_price = self._get_current_price(data, signal.timestamp)
                trade = self.trade_engine.execute_signal(signal, current_price)
                if trade:
                    trades.append(trade)
            
            logger.info(f"Executed {len(trades)} trades")
            
            # Calculate performance
            start_date = datetime.combine(config['start_date'], datetime.min.time())
            end_date = datetime.combine(config['end_date'], datetime.max.time())
            
            performance_metrics = self.performance_calculator.calculate_metrics(
                trades=trades,
                initial_capital=config['initial_capital'],
                start_date=start_date,
                end_date=end_date
            )
            
            # Get portfolio summary
            portfolio_summary = self.trade_engine.get_portfolio_summary()
            
            logger.info(f"Backtest completed: {performance_metrics['total_return_pct']:.2f}% return")
            
            return {
                'trades': trades,
                'performance_metrics': performance_metrics,
                'portfolio_summary': portfolio_summary,
                'engine_info': self.get_engine_info(),
                'data_info': self.get_data_info(data),
                'signals_count': len(signals),
                'trades_count': len(trades)
            }
            
        except Exception as e:
            logger.error(f"Error in custom engine backtest: {e}")
            raise
    
    def get_required_dependencies(self) -> List[str]:
        """
        Return list of required Python packages for this engine
        
        Returns:
            List of package names
        """
        return [
            'polars',
            'numpy',
            'pydantic',
            'pydantic-settings'
        ]
    
    def validate_strategy(self, strategy: Any) -> bool:
        """
        Validate that the strategy is compatible with this engine
        
        Args:
            strategy: Strategy instance
            
        Returns:
            True if strategy is compatible
        """
        try:
            # Check if strategy has required methods
            required_methods = ['initialize', 'evaluate_entry', 'evaluate_exit', 'generate_signals']
            
            for method_name in required_methods:
                if not hasattr(strategy, method_name):
                    logger.warning(f"Strategy missing required method: {method_name}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating strategy: {e}")
            return False
    
    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about this engine
        
        Returns:
            Dictionary with engine information
        """
        return {
            'name': 'Custom Backtesting Engine',
            'version': '1.0.0',
            'description': 'Custom backtesting engine with signal generation, trade execution, and performance calculation',
            'capabilities': [
                'Signal generation',
                'Trade execution',
                'Performance metrics',
                'Portfolio management',
                'Risk management'
            ],
            'supported_data_formats': ['polars.DataFrame'],
            'supported_strategy_types': ['custom_strategy_base']
        }
    
    def _get_current_price(self, data: pl.DataFrame, timestamp: datetime) -> float:
        """
        Get current price for a given timestamp
        
        Args:
            data: OHLCV data
            timestamp: Target timestamp
            
        Returns:
            Current price
        """
        try:
            # Find the row with the closest timestamp
            filtered_data = data.filter(data['timestamp'] == timestamp)
            
            if len(filtered_data) > 0:
                return filtered_data['close'][0]
            else:
                # If exact timestamp not found, get the last available price
                return data['close'][-1]
                
        except Exception as e:
            logger.warning(f"Error getting current price for {timestamp}: {e}")
            return 0.0

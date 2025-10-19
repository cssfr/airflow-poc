import logging
from typing import List, Dict, Any
import polars as pl
from strategies.base import StrategyBase, TradeSignal, TradeType
from datetime import datetime

logger = logging.getLogger(__name__)


class SignalEngine:
    """
    Engine responsible for generating trading signals from strategies
    """
    
    def __init__(self):
        self.signals: List[TradeSignal] = []
    
    def generate_signals(self, strategy: StrategyBase, data: pl.DataFrame) -> List[TradeSignal]:
        """
        Generate trading signals using a strategy
        
        Args:
            strategy: Strategy instance to use
            data: OHLCV data
            
        Returns:
            List of generated signals
        """
        try:
            # Initialize strategy with data
            strategy.initialize(data)
            
            # Generate signals
            signals = strategy.generate_signals()
            
            logger.info(f"Generated {len(signals)} signals using {strategy.name}")
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            raise
    
    def validate_signal(self, signal: TradeSignal, data: pl.DataFrame) -> bool:
        """
        Validate a trading signal
        
        Args:
            signal: Signal to validate
            data: OHLCV data for validation
            
        Returns:
            True if signal is valid
        """
        try:
            # Check if timestamp exists in data
            timestamp_exists = data.filter(pl.col('timestamp') == signal.timestamp).height > 0
            
            if not timestamp_exists:
                logger.warning(f"Signal timestamp {signal.timestamp} not found in data")
                return False
            
            # Check price is positive
            if signal.price <= 0:
                logger.warning(f"Invalid price {signal.price} in signal")
                return False
            
            # Check quantity is positive
            if signal.quantity <= 0:
                logger.warning(f"Invalid quantity {signal.quantity} in signal")
                return False
            
            # Check symbol matches
            if signal.symbol not in data.columns:
                logger.warning(f"Symbol {signal.symbol} not found in data")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            return False
    
    def filter_signals(self, signals: List[TradeSignal], data: pl.DataFrame) -> List[TradeSignal]:
        """
        Filter out invalid signals
        
        Args:
            signals: List of signals to filter
            data: OHLCV data for validation
            
        Returns:
            List of valid signals
        """
        valid_signals = []
        
        for signal in signals:
            if self.validate_signal(signal, data):
                valid_signals.append(signal)
            else:
                logger.warning(f"Filtered out invalid signal: {signal}")
        
        logger.info(f"Filtered {len(signals)} signals to {len(valid_signals)} valid signals")
        return valid_signals
    
    def get_signals_by_type(self, signals: List[TradeSignal], trade_type: TradeType) -> List[TradeSignal]:
        """
        Get signals of a specific type
        
        Args:
            signals: List of signals
            trade_type: Type of signals to filter
            
        Returns:
            List of signals of the specified type
        """
        return [s for s in signals if s.trade_type == trade_type]
    
    def get_signals_by_symbol(self, signals: List[TradeSignal], symbol: str) -> List[TradeSignal]:
        """
        Get signals for a specific symbol
        
        Args:
            signals: List of signals
            symbol: Symbol to filter by
            
        Returns:
            List of signals for the specified symbol
        """
        return [s for s in signals if s.symbol == symbol]
    
    def get_signals_in_timeframe(
        self, 
        signals: List[TradeSignal], 
        start_time: datetime, 
        end_time: datetime
    ) -> List[TradeSignal]:
        """
        Get signals within a specific timeframe
        
        Args:
            signals: List of signals
            start_time: Start of timeframe
            end_time: End of timeframe
            
        Returns:
            List of signals within the timeframe
        """
        return [
            s for s in signals 
            if start_time <= s.timestamp <= end_time
        ]
    
    def sort_signals_by_time(self, signals: List[TradeSignal]) -> List[TradeSignal]:
        """
        Sort signals by timestamp
        
        Args:
            signals: List of signals to sort
            
        Returns:
            Sorted list of signals
        """
        return sorted(signals, key=lambda x: x.timestamp)
    
    def get_signal_summary(self, signals: List[TradeSignal]) -> Dict[str, Any]:
        """
        Get summary statistics for signals
        
        Args:
            signals: List of signals
            
        Returns:
            Dictionary with signal statistics
        """
        if not signals:
            return {
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'symbols': [],
                'timeframe': None
            }
        
        buy_signals = self.get_signals_by_type(signals, TradeType.BUY)
        sell_signals = self.get_signals_by_type(signals, TradeType.SELL)
        
        symbols = list(set(s.symbol for s in signals))
        timeframes = [s.timestamp for s in signals]
        
        return {
            'total_signals': len(signals),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'symbols': symbols,
            'earliest_signal': min(timeframes) if timeframes else None,
            'latest_signal': max(timeframes) if timeframes else None,
            'timeframe_days': (max(timeframes) - min(timeframes)).days if len(timeframes) > 1 else 0
        }
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import polars as pl
from enum import Enum


class TradeType(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class TradeSignal:
    """Represents a trading signal"""
    timestamp: datetime
    symbol: str
    trade_type: TradeType
    price: float
    quantity: float
    reason: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class StrategyParameters:
    """Base class for strategy parameters"""
    pass


class StrategyBase(ABC):
    """
    Abstract base class for all trading strategies
    
    All strategies must implement the required methods:
    - initialize(): Set up strategy with data and parameters
    - evaluate_entry(): Determine if we should enter a position
    - evaluate_exit(): Determine if we should exit a position
    - generate_signals(): Main signal generation logic
    """
    
    def __init__(self, parameters: StrategyParameters):
        self.parameters = parameters
        self.data: Optional[pl.DataFrame] = None
        self.initialized = False
        self.name = self.__class__.__name__
    
    @abstractmethod
    def initialize(self, data: pl.DataFrame) -> None:
        """
        Initialize the strategy with historical data
        
        Args:
            data: OHLCV data as Polars DataFrame with columns:
                  ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        pass
    
    @abstractmethod
    def evaluate_entry(self, current_data: pl.DataFrame, current_index: int) -> Optional[TradeSignal]:
        """
        Evaluate if we should enter a position
        
        Args:
            current_data: Historical data up to current point
            current_index: Current row index in the data
            
        Returns:
            TradeSignal if we should enter, None otherwise
        """
        pass
    
    @abstractmethod
    def evaluate_exit(self, current_data: pl.DataFrame, current_index: int, position: Dict[str, Any]) -> Optional[TradeSignal]:
        """
        Evaluate if we should exit a position
        
        Args:
            current_data: Historical data up to current point
            current_index: Current row index in the data
            position: Current position information
            
        Returns:
            TradeSignal if we should exit, None otherwise
        """
        pass
    
    @abstractmethod
    def generate_signals(self) -> List[TradeSignal]:
        """
        Generate all trading signals for the strategy
        
        Returns:
            List of TradeSignal objects
        """
        pass
    
    def validate_data(self, data: pl.DataFrame) -> None:
        """Validate that data has required columns"""
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"Data missing required column: {col}")
        
        if len(data) == 0:
            raise ValueError("Data is empty")
    
    def get_data_slice(self, end_index: int, lookback: int = 0) -> pl.DataFrame:
        """
        Get a slice of data up to a specific index
        
        Args:
            end_index: End index (exclusive)
            lookback: Number of additional rows to include before end_index
            
        Returns:
            Data slice as Polars DataFrame
        """
        if self.data is None:
            raise ValueError("Strategy not initialized with data")
        
        start_index = max(0, end_index - lookback)
        return self.data.slice(start_index, end_index - start_index)
    
    def get_current_price(self, index: int, price_type: str = 'close') -> float:
        """
        Get current price at a specific index
        
        Args:
            index: Data index
            price_type: Type of price ('open', 'high', 'low', 'close')
            
        Returns:
            Price value
        """
        if self.data is None:
            raise ValueError("Strategy not initialized with data")
        
        if index >= len(self.data):
            raise IndexError(f"Index {index} out of range")
        
        return self.data[price_type][index]
    
    def get_current_timestamp(self, index: int) -> datetime:
        """Get current timestamp at a specific index"""
        if self.data is None:
            raise ValueError("Strategy not initialized with data")
        
        if index >= len(self.data):
            raise IndexError(f"Index {index} out of range")
        
        return self.data['timestamp'][index]
    
    def __str__(self) -> str:
        return f"{self.name}({self.parameters})"
    
    def __repr__(self) -> str:
        return self.__str__()


# Example parameter classes for common strategies
@dataclass
class MovingAverageParameters(StrategyParameters):
    """Parameters for moving average strategies"""
    short_window: int = 10
    long_window: int = 20
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.04


@dataclass
class RSIStrategyParameters(StrategyParameters):
    """Parameters for RSI strategies"""
    rsi_period: int = 14
    oversold_threshold: float = 30.0
    overbought_threshold: float = 70.0
    stop_loss_pct: float = 0.02


@dataclass
class ORBStrategyParameters(StrategyParameters):
    """Parameters for Opening Range Breakout strategies"""
    orb_minutes: int = 15
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.04
    min_volume_threshold: float = 1000.0
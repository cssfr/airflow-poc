#!/usr/bin/env python3
"""
Seed script to populate built-in strategies in Supabase
"""

import sys
import os
import logging
from datetime import datetime

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_client import supabase_client

logger = logging.getLogger(__name__)


def get_dax_london_bracket_strategy():
    """DAX London Bracket Strategy code"""
    return '''
from strategies.base import StrategyBase, TradeSignal, TradeType, StrategyParameters
from datetime import datetime, time
import polars as pl

class DAXLondonBracketParameters(StrategyParameters):
    def __init__(self, orb_minutes=15, stop_loss_pct=0.02, take_profit_pct=0.04, min_volume_threshold=1000.0):
        self.orb_minutes = orb_minutes
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.min_volume_threshold = min_volume_threshold

class DAXLondonBracketStrategy(StrategyBase):
    def __init__(self, parameters: DAXLondonBracketParameters):
        super().__init__(parameters)
        self.orb_high = None
        self.orb_low = None
        self.orb_volume = None
        self.position = None
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
    
    def initialize(self, data: pl.DataFrame) -> None:
        """Initialize strategy with data"""
        self.validate_data(data)
        self.data = data
        self.initialized = True
        logger.info(f"Initialized {self.name} with {len(data)} data points")
    
    def evaluate_entry(self, current_data: pl.DataFrame, current_index: int) -> TradeSignal:
        """Evaluate entry conditions"""
        if self.position is not None:
            return None
        
        current_row = current_data.row(current_index, named=True)
        current_time = current_row['timestamp'].time()
        
        # Check if we're in London session (8:00-16:30 CET)
        if not (time(8, 0) <= current_time <= time(16, 30)):
            return None
        
        # Calculate ORB if not done yet
        if self.orb_high is None:
            self._calculate_orb(current_data, current_index)
        
        if self.orb_high is None:
            return None
        
        # Check volume threshold
        if current_row['volume'] < self.parameters.min_volume_threshold:
            return None
        
        # Check for breakout
        if current_row['high'] > self.orb_high:
            # Bullish breakout
            return TradeSignal(
                timestamp=current_row['timestamp'],
                symbol=current_row.get('symbol', 'DAX'),
                trade_type=TradeType.BUY,
                price=self.orb_high,
                quantity=1.0,
                reason=f"Bullish ORB breakout above {self.orb_high}",
                metadata={'orb_high': self.orb_high, 'orb_low': self.orb_low}
            )
        elif current_row['low'] < self.orb_low:
            # Bearish breakout
            return TradeSignal(
                timestamp=current_row['timestamp'],
                symbol=current_row.get('symbol', 'DAX'),
                trade_type=TradeType.SELL,
                price=self.orb_low,
                quantity=1.0,
                reason=f"Bearish ORB breakout below {self.orb_low}",
                metadata={'orb_high': self.orb_high, 'orb_low': self.orb_low}
            )
        
        return None
    
    def evaluate_exit(self, current_data: pl.DataFrame, current_index: int, position: dict) -> TradeSignal:
        """Evaluate exit conditions"""
        if self.position is None:
            return None
        
        current_row = current_data.row(current_index, named=True)
        current_price = current_row['close']
        
        # Check stop loss
        if self.position['type'] == 'long' and current_price <= self.stop_loss:
            return TradeSignal(
                timestamp=current_row['timestamp'],
                symbol=current_row.get('symbol', 'DAX'),
                trade_type=TradeType.SELL,
                price=current_price,
                quantity=self.position['quantity'],
                reason=f"Stop loss hit at {current_price}",
                metadata={'stop_loss': self.stop_loss}
            )
        elif self.position['type'] == 'short' and current_price >= self.stop_loss:
            return TradeSignal(
                timestamp=current_row['timestamp'],
                symbol=current_row.get('symbol', 'DAX'),
                trade_type=TradeType.BUY,
                price=current_price,
                quantity=self.position['quantity'],
                reason=f"Stop loss hit at {current_price}",
                metadata={'stop_loss': self.stop_loss}
            )
        
        # Check take profit
        if self.position['type'] == 'long' and current_price >= self.take_profit:
            return TradeSignal(
                timestamp=current_row['timestamp'],
                symbol=current_row.get('symbol', 'DAX'),
                trade_type=TradeType.SELL,
                price=current_price,
                quantity=self.position['quantity'],
                reason=f"Take profit hit at {current_price}",
                metadata={'take_profit': self.take_profit}
            )
        elif self.position['type'] == 'short' and current_price <= self.take_profit:
            return TradeSignal(
                timestamp=current_row['timestamp'],
                symbol=current_row.get('symbol', 'DAX'),
                trade_type=TradeType.BUY,
                price=current_price,
                quantity=self.position['quantity'],
                reason=f"Take profit hit at {current_price}",
                metadata={'take_profit': self.take_profit}
            )
        
        return None
    
    def generate_signals(self) -> list:
        """Generate all signals for the strategy"""
        if not self.initialized:
            raise ValueError("Strategy not initialized")
        
        signals = []
        
        for i in range(len(self.data)):
            current_data = self.get_data_slice(i + 1)
            
            # Check for entry
            entry_signal = self.evaluate_entry(current_data, i)
            if entry_signal:
                signals.append(entry_signal)
                # Set position and levels
                self._set_position(entry_signal)
            
            # Check for exit if in position
            if self.position is not None:
                exit_signal = self.evaluate_exit(current_data, i, self.position)
                if exit_signal:
                    signals.append(exit_signal)
                    self._clear_position()
        
        return signals
    
    def _calculate_orb(self, data: pl.DataFrame, current_index: int) -> None:
        """Calculate Opening Range Breakout levels"""
        # Get first N minutes of data
        orb_data = data.slice(0, min(current_index + 1, self.parameters.orb_minutes))
        
        if len(orb_data) == 0:
            return
        
        self.orb_high = orb_data['high'].max()
        self.orb_low = orb_data['low'].min()
        self.orb_volume = orb_data['volume'].sum()
    
    def _set_position(self, signal: TradeSignal) -> None:
        """Set position after entry"""
        self.position = {
            'type': 'long' if signal.trade_type == TradeType.BUY else 'short',
            'quantity': signal.quantity,
            'entry_time': signal.timestamp
        }
        self.entry_price = signal.price
        
        # Set stop loss and take profit
        if signal.trade_type == TradeType.BUY:
            self.stop_loss = signal.price * (1 - self.parameters.stop_loss_pct)
            self.take_profit = signal.price * (1 + self.parameters.take_profit_pct)
        else:
            self.stop_loss = signal.price * (1 + self.parameters.stop_loss_pct)
            self.take_profit = signal.price * (1 - self.parameters.take_profit_pct)
    
    def _clear_position(self) -> None:
        """Clear position after exit"""
        self.position = None
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
'''


def get_simple_orb_strategy():
    """Simple Opening Range Breakout Strategy code"""
    return '''
from strategies.base import StrategyBase, TradeSignal, TradeType, StrategyParameters
from datetime import datetime, time
import polars as pl

class SimpleORBParameters(StrategyParameters):
    def __init__(self, orb_minutes=15, stop_loss_pct=0.02, take_profit_pct=0.04):
        self.orb_minutes = orb_minutes
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

class SimpleORBStrategy(StrategyBase):
    def __init__(self, parameters: SimpleORBParameters):
        super().__init__(parameters)
        self.orb_high = None
        self.orb_low = None
        self.position = None
        self.entry_price = None
    
    def initialize(self, data: pl.DataFrame) -> None:
        """Initialize strategy with data"""
        self.validate_data(data)
        self.data = data
        self.initialized = True
        logger.info(f"Initialized {self.name} with {len(data)} data points")
    
    def evaluate_entry(self, current_data: pl.DataFrame, current_index: int) -> TradeSignal:
        """Evaluate entry conditions"""
        if self.position is not None:
            return None
        
        current_row = current_data.row(current_index, named=True)
        
        # Calculate ORB if not done yet
        if self.orb_high is None:
            self._calculate_orb(current_data, current_index)
        
        if self.orb_high is None:
            return None
        
        # Check for breakout
        if current_row['high'] > self.orb_high:
            # Bullish breakout
            return TradeSignal(
                timestamp=current_row['timestamp'],
                symbol=current_row.get('symbol', 'UNKNOWN'),
                trade_type=TradeType.BUY,
                price=self.orb_high,
                quantity=1.0,
                reason=f"Bullish ORB breakout above {self.orb_high}",
                metadata={'orb_high': self.orb_high, 'orb_low': self.orb_low}
            )
        elif current_row['low'] < self.orb_low:
            # Bearish breakout
            return TradeSignal(
                timestamp=current_row['timestamp'],
                symbol=current_row.get('symbol', 'UNKNOWN'),
                trade_type=TradeType.SELL,
                price=self.orb_low,
                quantity=1.0,
                reason=f"Bearish ORB breakout below {self.orb_low}",
                metadata={'orb_high': self.orb_high, 'orb_low': self.orb_low}
            )
        
        return None
    
    def evaluate_exit(self, current_data: pl.DataFrame, current_index: int, position: dict) -> TradeSignal:
        """Evaluate exit conditions"""
        if self.position is None:
            return None
        
        current_row = current_data.row(current_index, named=True)
        current_price = current_row['close']
        
        # Simple exit after 1 hour
        if (current_row['timestamp'] - self.position['entry_time']).total_seconds() > 3600:
            return TradeSignal(
                timestamp=current_row['timestamp'],
                symbol=current_row.get('symbol', 'UNKNOWN'),
                trade_type=TradeType.SELL if self.position['type'] == 'long' else TradeType.BUY,
                price=current_price,
                quantity=self.position['quantity'],
                reason="Time-based exit after 1 hour",
                metadata={'entry_time': self.position['entry_time']}
            )
        
        return None
    
    def generate_signals(self) -> list:
        """Generate all signals for the strategy"""
        if not self.initialized:
            raise ValueError("Strategy not initialized")
        
        signals = []
        
        for i in range(len(self.data)):
            current_data = self.get_data_slice(i + 1)
            
            # Check for entry
            entry_signal = self.evaluate_entry(current_data, i)
            if entry_signal:
                signals.append(entry_signal)
                # Set position
                self._set_position(entry_signal)
            
            # Check for exit if in position
            if self.position is not None:
                exit_signal = self.evaluate_exit(current_data, i, self.position)
                if exit_signal:
                    signals.append(exit_signal)
                    self._clear_position()
        
        return signals
    
    def _calculate_orb(self, data: pl.DataFrame, current_index: int) -> None:
        """Calculate Opening Range Breakout levels"""
        # Get first N minutes of data
        orb_data = data.slice(0, min(current_index + 1, self.parameters.orb_minutes))
        
        if len(orb_data) == 0:
            return
        
        self.orb_high = orb_data['high'].max()
        self.orb_low = orb_data['low'].min()
    
    def _set_position(self, signal: TradeSignal) -> None:
        """Set position after entry"""
        self.position = {
            'type': 'long' if signal.trade_type == TradeType.BUY else 'short',
            'quantity': signal.quantity,
            'entry_time': signal.timestamp
        }
        self.entry_price = signal.price
    
    def _clear_position(self) -> None:
        """Clear position after exit"""
        self.position = None
        self.entry_price = None
'''


def seed_strategies():
    """Seed built-in strategies into Supabase"""
    try:
        # Test connection first
        if not supabase_client.test_connection():
            logger.error("Failed to connect to Supabase")
            return False
        
        # Define strategies to seed (matching your schema)
        strategies_to_seed = [
            {
                'name': 'DAX London Bracket Strategy',
                'description': 'Opening Range Breakout strategy optimized for DAX during London session',
                'code_content': get_dax_london_bracket_strategy(),
                'strategy_class': 'DAXLondonBracketStrategy',
                'parameters': {  # Your schema uses 'parameters' instead of 'parameter_schema'
                    'orb_minutes': {'type': 'integer', 'default': 15, 'min': 5, 'max': 60},
                    'stop_loss_pct': {'type': 'float', 'default': 0.02, 'min': 0.001, 'max': 0.1},
                    'take_profit_pct': {'type': 'float', 'default': 0.04, 'min': 0.001, 'max': 0.2},
                    'min_volume_threshold': {'type': 'float', 'default': 1000.0, 'min': 0, 'max': 10000}
                },
                'engine_type': 'custom',  # Use custom engine
                'engine_config': {
                    'commission_rate': 0.001,
                    'slippage': 0.0001
                },
                'is_public': True
            },
            {
                'name': 'Simple ORB Strategy',
                'description': 'Simple Opening Range Breakout strategy for any symbol',
                'code_content': get_simple_orb_strategy(),
                'strategy_class': 'SimpleORBStrategy',
                'parameters': {  # Your schema uses 'parameters' instead of 'parameter_schema'
                    'orb_minutes': {'type': 'integer', 'default': 15, 'min': 5, 'max': 60},
                    'stop_loss_pct': {'type': 'float', 'default': 0.02, 'min': 0.001, 'max': 0.1},
                    'take_profit_pct': {'type': 'float', 'default': 0.04, 'min': 0.001, 'max': 0.2}
                },
                'engine_type': 'custom',  # Use custom engine
                'engine_config': {
                    'commission_rate': 0.001,
                    'slippage': 0.0001
                },
                'is_public': True
            }
        ]
        
        # Insert strategies
        for strategy_data in strategies_to_seed:
            try:
                # Check if strategy already exists
                existing = supabase_client.client.table('strategies').select('id').eq('name', strategy_data['name']).execute()
                
                if existing.data:
                    logger.info(f"Strategy '{strategy_data['name']}' already exists, skipping")
                    continue
                
                # Insert new strategy
                result = supabase_client.client.table('strategies').insert(strategy_data).execute()
                
                if result.data:
                    logger.info(f"Successfully seeded strategy: {strategy_data['name']}")
                else:
                    logger.error(f"Failed to seed strategy: {strategy_data['name']}")
                    
            except Exception as e:
                logger.error(f"Error seeding strategy '{strategy_data['name']}': {e}")
        
        logger.info("Strategy seeding completed")
        return True
        
    except Exception as e:
        logger.error(f"Error in seed_strategies: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = seed_strategies()
    sys.exit(0 if success else 1)
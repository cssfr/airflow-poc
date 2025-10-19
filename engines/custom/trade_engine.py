import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from strategies.base import TradeSignal, TradeType

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    quantity: float
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Trade:
    """Represents a completed trade"""
    symbol: str
    trade_type: TradeType
    quantity: float
    price: float
    timestamp: datetime
    pnl: float = 0.0
    fees: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class TradeEngine:
    """
    Engine responsible for executing trades and managing positions
    """
    
    def __init__(self, initial_capital: float = 10000.0, commission_rate: float = 0.001):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.commission_rate = commission_rate
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.cash = initial_capital
        
        logger.info(f"Initialized TradeEngine with capital: ${initial_capital:,.2f}")
    
    def execute_signal(self, signal: TradeSignal, current_price: float) -> Optional[Trade]:
        """
        Execute a trading signal
        
        Args:
            signal: Trading signal to execute
            current_price: Current market price
            
        Returns:
            Trade object if executed, None if not executed
        """
        try:
            # Calculate commission
            trade_value = signal.quantity * current_price
            commission = trade_value * self.commission_rate
            
            if signal.trade_type == TradeType.BUY:
                return self._execute_buy(signal, current_price, commission)
            elif signal.trade_type == TradeType.SELL:
                return self._execute_sell(signal, current_price, commission)
            else:
                logger.warning(f"Unknown trade type: {signal.trade_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return None
    
    def _execute_buy(self, signal: TradeSignal, price: float, commission: float) -> Optional[Trade]:
        """Execute a buy order"""
        try:
            total_cost = (signal.quantity * price) + commission
            
            # Check if we have enough cash
            if total_cost > self.cash:
                logger.warning(f"Insufficient cash for buy order. Required: ${total_cost:,.2f}, Available: ${self.cash:,.2f}")
                return None
            
            # Execute the trade
            trade = Trade(
                symbol=signal.symbol,
                trade_type=TradeType.BUY,
                quantity=signal.quantity,
                price=price,
                timestamp=signal.timestamp,
                fees=commission,
                metadata=signal.metadata
            )
            
            # Update cash and position
            self.cash -= total_cost
            self._update_position(signal.symbol, signal.quantity, price, signal.timestamp)
            self.trades.append(trade)
            
            logger.info(f"Executed BUY: {signal.quantity} {signal.symbol} @ ${price:.2f}")
            return trade
            
        except Exception as e:
            logger.error(f"Error executing buy order: {e}")
            return None
    
    def _execute_sell(self, signal: TradeSignal, price: float, commission: float) -> Optional[Trade]:
        """Execute a sell order"""
        try:
            # Check if we have the position
            if signal.symbol not in self.positions:
                logger.warning(f"No position to sell for {signal.symbol}")
                return None
            
            position = self.positions[signal.symbol]
            
            # Check if we have enough quantity
            if signal.quantity > position.quantity:
                logger.warning(f"Insufficient quantity to sell. Required: {signal.quantity}, Available: {position.quantity}")
                return None
            
            # Calculate PnL
            pnl = (price - position.entry_price) * signal.quantity - commission
            
            # Execute the trade
            trade = Trade(
                symbol=signal.symbol,
                trade_type=TradeType.SELL,
                quantity=signal.quantity,
                price=price,
                timestamp=signal.timestamp,
                pnl=pnl,
                fees=commission,
                metadata=signal.metadata
            )
            
            # Update cash and position
            self.cash += (signal.quantity * price) - commission
            self._update_position(signal.symbol, -signal.quantity, price, signal.timestamp)
            self.trades.append(trade)
            
            logger.info(f"Executed SELL: {signal.quantity} {signal.symbol} @ ${price:.2f}, PnL: ${pnl:.2f}")
            return trade
            
        except Exception as e:
            logger.error(f"Error executing sell order: {e}")
            return None
    
    def _update_position(self, symbol: str, quantity_change: float, price: float, timestamp: datetime) -> None:
        """Update position after a trade"""
        if symbol not in self.positions:
            # Create new position
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity_change,
                entry_price=price,
                entry_time=timestamp,
                current_price=price
            )
        else:
            # Update existing position
            position = self.positions[symbol]
            
            if position.quantity + quantity_change == 0:
                # Position closed
                del self.positions[symbol]
            else:
                # Update position
                total_value = (position.quantity * position.entry_price) + (quantity_change * price)
                new_quantity = position.quantity + quantity_change
                
                if new_quantity != 0:
                    position.quantity = new_quantity
                    position.entry_price = total_value / new_quantity
                    position.current_price = price
                    position.unrealized_pnl = (price - position.entry_price) * new_quantity
    
    def update_positions(self, current_prices: Dict[str, float]) -> None:
        """Update current prices and unrealized PnL for all positions"""
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                position.current_price = current_prices[symbol]
                position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
    
    def get_portfolio_value(self) -> float:
        """Get total portfolio value"""
        total_value = self.cash
        
        for position in self.positions.values():
            total_value += position.quantity * position.current_price
        
        return total_value
    
    def get_total_pnl(self) -> float:
        """Get total realized and unrealized PnL"""
        realized_pnl = sum(trade.pnl for trade in self.trades)
        unrealized_pnl = sum(position.unrealized_pnl for position in self.positions.values())
        
        return realized_pnl + unrealized_pnl
    
    def get_trades_by_symbol(self, symbol: str) -> List[Trade]:
        """Get all trades for a specific symbol"""
        return [trade for trade in self.trades if trade.symbol == symbol]
    
    def get_trades_by_type(self, trade_type: TradeType) -> List[Trade]:
        """Get all trades of a specific type"""
        return [trade for trade in self.trades if trade.trade_type == trade_type]
    
    def get_trades_in_timeframe(self, start_time: datetime, end_time: datetime) -> List[Trade]:
        """Get trades within a specific timeframe"""
        return [
            trade for trade in self.trades
            if start_time <= trade.timestamp <= end_time
        ]
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary statistics"""
        total_trades = len(self.trades)
        buy_trades = len(self.get_trades_by_type(TradeType.BUY))
        sell_trades = len(self.get_trades_by_type(TradeType.SELL))
        
        total_fees = sum(trade.fees for trade in self.trades)
        total_pnl = self.get_total_pnl()
        portfolio_value = self.get_portfolio_value()
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.cash,
            'portfolio_value': portfolio_value,
            'total_return': (portfolio_value - self.initial_capital) / self.initial_capital,
            'total_pnl': total_pnl,
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'total_fees': total_fees,
            'active_positions': len(self.positions),
            'positions': {symbol: {
                'quantity': pos.quantity,
                'entry_price': pos.entry_price,
                'current_price': pos.current_price,
                'unrealized_pnl': pos.unrealized_pnl
            } for symbol, pos in self.positions.items()}
        }
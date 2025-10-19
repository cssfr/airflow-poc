import logging
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime, timedelta
from engines.trade_engine import Trade, TradeType

logger = logging.getLogger(__name__)


class PerformanceCalculator:
    """
    Engine responsible for calculating performance metrics
    """
    
    def __init__(self):
        pass
    
    def calculate_metrics(
        self, 
        trades: List[Trade], 
        initial_capital: float,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics
        
        Args:
            trades: List of completed trades
            initial_capital: Starting capital
            start_date: Backtest start date
            end_date: Backtest end date
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            if not trades:
                return self._get_empty_metrics(initial_capital, start_date, end_date)
            
            # Basic metrics
            total_return = self._calculate_total_return(trades, initial_capital)
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.pnl > 0])
            losing_trades = len([t for t in trades if t.pnl < 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # PnL metrics
            total_pnl = sum(trade.pnl for trade in trades)
            avg_win = np.mean([t.pnl for t in trades if t.pnl > 0]) if winning_trades > 0 else 0
            avg_loss = np.mean([t.pnl for t in trades if t.pnl < 0]) if losing_trades > 0 else 0
            profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else float('inf')
            
            # Risk metrics
            max_drawdown = self._calculate_max_drawdown(trades, initial_capital)
            sharpe_ratio = self._calculate_sharpe_ratio(trades, start_date, end_date)
            
            # Trade analysis
            trade_analysis = self._analyze_trades(trades)
            
            metrics = {
                'total_return': total_return,
                'total_return_pct': total_return * 100,
                'total_pnl': total_pnl,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'win_rate_pct': win_rate * 100,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'max_drawdown': max_drawdown,
                'max_drawdown_pct': max_drawdown * 100,
                'sharpe_ratio': sharpe_ratio,
                'start_date': start_date,
                'end_date': end_date,
                'duration_days': (end_date - start_date).days,
                'trade_analysis': trade_analysis
            }
            
            logger.info(f"Calculated performance metrics: {total_return:.2%} return, {win_rate:.1%} win rate")
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            raise
    
    def _calculate_total_return(self, trades: List[Trade], initial_capital: float) -> float:
        """Calculate total return percentage"""
        total_pnl = sum(trade.pnl for trade in trades)
        return total_pnl / initial_capital if initial_capital > 0 else 0
    
    def _calculate_max_drawdown(self, trades: List[Trade], initial_capital: float) -> float:
        """Calculate maximum drawdown"""
        if not trades:
            return 0.0
        
        # Calculate running portfolio value
        portfolio_values = [initial_capital]
        current_value = initial_capital
        
        for trade in trades:
            current_value += trade.pnl
            portfolio_values.append(current_value)
        
        # Calculate drawdowns
        peak = portfolio_values[0]
        max_dd = 0.0
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def _calculate_sharpe_ratio(self, trades: List[Trade], start_date: datetime, end_date: datetime) -> float:
        """Calculate Sharpe ratio (simplified version)"""
        if len(trades) < 2:
            return 0.0
        
        # Calculate daily returns
        daily_returns = []
        current_value = 10000  # Starting value
        
        # Sort trades by timestamp
        sorted_trades = sorted(trades, key=lambda x: x.timestamp)
        
        # Group trades by day and calculate daily returns
        current_day = start_date.date()
        end_day = end_date.date()
        day_pnl = 0
        
        for trade in sorted_trades:
            trade_day = trade.timestamp.date()
            
            if trade_day > current_day:
                # New day, calculate return
                if current_value > 0:
                    daily_return = day_pnl / current_value
                    daily_returns.append(daily_return)
                
                current_value += day_pnl
                day_pnl = trade.pnl
                current_day = trade_day
            else:
                day_pnl += trade.pnl
        
        # Add final day
        if current_value > 0:
            daily_return = day_pnl / current_value
            daily_returns.append(daily_return)
        
        if len(daily_returns) < 2:
            return 0.0
        
        # Calculate Sharpe ratio (assuming risk-free rate = 0)
        mean_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)
        
        if std_return == 0:
            return 0.0
        
        # Annualize (assuming 252 trading days)
        sharpe_ratio = (mean_return / std_return) * np.sqrt(252)
        return sharpe_ratio
    
    def _analyze_trades(self, trades: List[Trade]) -> Dict[str, Any]:
        """Analyze trade patterns"""
        if not trades:
            return {}
        
        # Group by symbol
        symbol_trades = {}
        for trade in trades:
            if trade.symbol not in symbol_trades:
                symbol_trades[trade.symbol] = []
            symbol_trades[trade.symbol].append(trade)
        
        # Calculate metrics per symbol
        symbol_metrics = {}
        for symbol, symbol_trade_list in symbol_trades.items():
            symbol_pnl = sum(t.pnl for t in symbol_trade_list)
            symbol_win_rate = len([t for t in symbol_trade_list if t.pnl > 0]) / len(symbol_trade_list)
            
            symbol_metrics[symbol] = {
                'total_trades': len(symbol_trade_list),
                'total_pnl': symbol_pnl,
                'win_rate': symbol_win_rate,
                'avg_pnl': symbol_pnl / len(symbol_trade_list)
            }
        
        # Time analysis
        trade_times = [t.timestamp for t in trades]
        if trade_times:
            first_trade = min(trade_times)
            last_trade = max(trade_times)
            trading_days = (last_trade - first_trade).days + 1
            trades_per_day = len(trades) / trading_days if trading_days > 0 else 0
        else:
            first_trade = None
            last_trade = None
            trading_days = 0
            trades_per_day = 0
        
        return {
            'symbol_metrics': symbol_metrics,
            'first_trade': first_trade,
            'last_trade': last_trade,
            'trading_days': trading_days,
            'trades_per_day': trades_per_day,
            'total_fees': sum(t.fees for t in trades)
        }
    
    def _get_empty_metrics(self, initial_capital: float, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Return empty metrics when no trades"""
        return {
            'total_return': 0.0,
            'total_return_pct': 0.0,
            'total_pnl': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'win_rate_pct': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'max_drawdown_pct': 0.0,
            'sharpe_ratio': 0.0,
            'start_date': start_date,
            'end_date': end_date,
            'duration_days': (end_date - start_date).days,
            'trade_analysis': {}
        }
    
    def calculate_rolling_metrics(
        self, 
        trades: List[Trade], 
        initial_capital: float,
        window_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Calculate rolling performance metrics
        
        Args:
            trades: List of trades
            initial_capital: Starting capital
            window_days: Rolling window size in days
            
        Returns:
            List of rolling metrics
        """
        if not trades:
            return []
        
        sorted_trades = sorted(trades, key=lambda x: x.timestamp)
        rolling_metrics = []
        
        for i, trade in enumerate(sorted_trades):
            window_start = trade.timestamp - timedelta(days=window_days)
            window_trades = [t for t in sorted_trades[:i+1] if t.timestamp >= window_start]
            
            if window_trades:
                metrics = self.calculate_metrics(window_trades, initial_capital, window_start, trade.timestamp)
                metrics['window_end'] = trade.timestamp
                rolling_metrics.append(metrics)
        
        return rolling_metrics
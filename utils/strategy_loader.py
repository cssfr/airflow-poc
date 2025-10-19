import types
import logging
from typing import Dict, Any, Type
from utils.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class StrategyLoader:
    def __init__(self):
        self.cache: Dict[str, Type] = {}
    
    def load_strategy(self, strategy_id: str) -> Type:
        """Load strategy class from Supabase code"""
        if strategy_id in self.cache:
            logger.info(f"Using cached strategy {strategy_id}")
            return self.cache[strategy_id]
        
        try:
            # Fetch strategy from Supabase
            strategy_def = supabase_client.get_strategy(strategy_id)
            
            # Load code dynamically
            strategy_class = self._load_from_code(
                strategy_def['code_content'],
                strategy_def['strategy_class']
            )
            
            self.cache[strategy_id] = strategy_class
            logger.info(f"Loaded strategy {strategy_def['name']} (class: {strategy_def['strategy_class']})")
            return strategy_class
            
        except Exception as e:
            logger.error(f"Error loading strategy {strategy_id}: {e}")
            raise
    
    def _load_from_code(self, code: str, class_name: str) -> Type:
        """Create module from code string and return the strategy class"""
        try:
            # Create a new module
            module = types.ModuleType('dynamic_strategy')
            
            # Execute the code in the module's namespace
            exec(code, module.__dict__)
            
            # Get the strategy class
            if not hasattr(module, class_name):
                raise ValueError(f"Class '{class_name}' not found in strategy code")
            
            strategy_class = getattr(module, class_name)
            
            # Validate that it's a proper strategy class
            self._validate_strategy_class(strategy_class)
            
            return strategy_class
            
        except Exception as e:
            logger.error(f"Error loading strategy class {class_name}: {e}")
            raise
    
    def _validate_strategy_class(self, strategy_class: Type) -> None:
        """Validate that the strategy class has required methods"""
        required_methods = [
            'initialize',
            'evaluate_entry', 
            'evaluate_exit',
            'generate_signals'
        ]
        
        for method_name in required_methods:
            if not hasattr(strategy_class, method_name):
                raise ValueError(f"Strategy class missing required method: {method_name}")
        
        logger.debug(f"Strategy class validation passed for {strategy_class.__name__}")
    
    def clear_cache(self) -> None:
        """Clear the strategy cache"""
        self.cache.clear()
        logger.info("Strategy cache cleared")
    
    def get_cached_strategies(self) -> list:
        """Get list of cached strategy IDs"""
        return list(self.cache.keys())


# Global strategy loader instance
strategy_loader = StrategyLoader()
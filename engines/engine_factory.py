import logging
from typing import Dict, Any, Type
from engines.base_engine import BaseEngine

logger = logging.getLogger(__name__)


class EngineFactory:
    """
    Factory class to create backtesting engines based on engine type.
    
    This allows the system to dynamically select the appropriate engine
    for each strategy without hardcoding engine types in the DAG.
    """
    
    # Registry of available engines
    _engines: Dict[str, Type[BaseEngine]] = {}
    
    @classmethod
    def register_engine(cls, engine_type: str, engine_class: Type[BaseEngine]):
        """
        Register a new engine type
        
        Args:
            engine_type: String identifier for the engine (e.g., 'custom', 'backtrader')
            engine_class: Engine class that implements BaseEngine
        """
        cls._engines[engine_type] = engine_class
        logger.info(f"Registered engine: {engine_type} -> {engine_class.__name__}")
    
    @classmethod
    def create_engine(cls, engine_type: str, config: Dict[str, Any]) -> BaseEngine:
        """
        Create an engine instance based on engine type
        
        Args:
            engine_type: Type of engine to create
            config: Engine-specific configuration
            
        Returns:
            Engine instance
            
        Raises:
            ValueError: If engine type is not registered
            ImportError: If required dependencies are not available
        """
        if engine_type not in cls._engines:
            available_engines = list(cls._engines.keys())
            raise ValueError(f"Unknown engine type: {engine_type}. Available engines: {available_engines}")
        
        engine_class = cls._engines[engine_type]
        
        try:
            # Create engine instance
            engine = engine_class(config)
            
            # Validate dependencies
            required_deps = engine.get_required_dependencies()
            cls._validate_dependencies(required_deps)
            
            logger.info(f"Created engine: {engine_type} -> {engine.name}")
            return engine
            
        except Exception as e:
            logger.error(f"Failed to create engine {engine_type}: {e}")
            raise
    
    @classmethod
    def _validate_dependencies(cls, dependencies: list):
        """
        Validate that required dependencies are available
        
        Args:
            dependencies: List of required package names
            
        Raises:
            ImportError: If any dependency is missing
        """
        for dep in dependencies:
            try:
                __import__(dep)
            except ImportError:
                raise ImportError(f"Required dependency '{dep}' is not installed")
    
    @classmethod
    def get_available_engines(cls) -> list:
        """
        Get list of available engine types
        
        Returns:
            List of registered engine types
        """
        return list(cls._engines.keys())
    
    @classmethod
    def get_engine_info(cls, engine_type: str) -> Dict[str, Any]:
        """
        Get information about a specific engine type
        
        Args:
            engine_type: Engine type to get info for
            
        Returns:
            Dictionary with engine information
        """
        if engine_type not in cls._engines:
            raise ValueError(f"Unknown engine type: {engine_type}")
        
        engine_class = cls._engines[engine_type]
        
        # Create temporary instance to get info
        temp_engine = engine_class({})
        
        return {
            'engine_type': engine_type,
            'engine_class': engine_class.__name__,
            'required_dependencies': temp_engine.get_required_dependencies(),
            'engine_info': temp_engine.get_engine_info()
        }


# Auto-register engines when this module is imported
def _register_default_engines():
    """Register default engines"""
    try:
        from engines.custom.custom_engine import CustomEngine
        EngineFactory.register_engine('custom', CustomEngine)
    except ImportError as e:
        logger.warning(f"Could not register custom engine: {e}")
    
    # Future engines can be registered here
    # try:
    #     from engines.backtrader.backtrader_engine import BacktraderEngine
    #     EngineFactory.register_engine('backtrader', BacktraderEngine)
    # except ImportError:
    #     pass


# Register engines when module is imported
_register_default_engines()

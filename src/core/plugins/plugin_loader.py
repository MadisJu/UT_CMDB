import importlib
import pkgutil
import src.core.plugins
from src.core.plugins.base_plugin import BasePlugin
import logging

logger = logging.getLogger(__name__)

"""This is to make new plugins loadable incase any kind of new data is required"""


def load_plugins():
    """
    Dynamically load all available plugins.
    
    Returns:
        Dictionary mapping plugin names to plugin instances
    """
    plugins = {}
    
    try:
        # Get the plugins package path
        plugins_path = src.core.plugins.__path__
        
        # Iterate through all modules in the plugins package
        for _, name, _ in pkgutil.iter_modules(plugins_path):
            # Skip __init__.py and base_plugin.py
            if name in ['__init__', 'base_plugin', 'plugin_loader']:
                continue
                
            try:
                # Import the module
                module_name = f"src.core.plugins.{name}"
                module = importlib.import_module(module_name)
                
                # Look for classes that inherit from BasePlugin
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    # Check if it's a class that inherits from BasePlugin
                    if (isinstance(attr, type) and 
                        issubclass(attr, BasePlugin) and 
                        attr is not BasePlugin):
                        
                        try:
                            # Instantiate the plugin
                            plugin_instance = attr()
                            plugins[plugin_instance.name] = plugin_instance
                            logger.info(f"Loaded plugin: {plugin_instance.name} - {plugin_instance.description}")
                            
                        except Exception as e:
                            logger.error(f"Failed to instantiate plugin {attr_name}: {e}")
                            
            except Exception as e:
                logger.error(f"Failed to load plugin module {name}: {e}")
                
    except Exception as e:
        logger.error(f"Error loading plugins: {e}")
    
    logger.info(f"Loaded {len(plugins)} plugins: {list(plugins.keys())}")
    return plugins


def get_plugin(plugin_name: str):
    """
    Get a specific plugin by name.
    
    Args:
        plugin_name: Name of the plugin to retrieve
        
    Returns:
        Plugin instance or None if not found
    """
    plugins = load_plugins()
    return plugins.get(plugin_name)


def list_available_plugins():
    """
    List all available plugin names.
    
    Returns:
        List of plugin names
    """
    plugins = load_plugins()
    return list(plugins.keys())
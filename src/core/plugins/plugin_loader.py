import importlib
import pkgutil
import src.core.plugins
from src.core.plugins.base_plugin import BasePlugin
import logging

logger = logging.getLogger(__name__)



def load_plugins():
    
    plugins = {}
    
    try:
        plugins_path = src.core.plugins.__path__
        
        for _, name, _ in pkgutil.iter_modules(plugins_path):
            if name in ['__init__', 'base_plugin', 'plugin_loader']:
                continue
                
            try:
                module_name = f"src.core.plugins.{name}"
                module = importlib.import_module(module_name)
                
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    if (isinstance(attr, type) and 
                        issubclass(attr, BasePlugin) and 
                        attr is not BasePlugin):
                        
                        try:
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
    plugins = load_plugins()
    return plugins.get(plugin_name)


def list_available_plugins():
    plugins = load_plugins()
    return list(plugins.keys())
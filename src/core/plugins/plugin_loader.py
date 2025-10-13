import importlib
import pkgutil
import src.core.plugins

"""This is to make new plugins loadable incase any kind of new data is required"""


def load_plugins():
    plugins = {}
    for _, name, _ in pkgutil.iter_modules(src.core.plugins.__path__):
        module = importlib.import_module(f"core.plugins.{name}")
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, plugins.BasePlugin) and obj is not plugins.BasePlugin:
                plugin = obj()
                plugins[plugin.name] = plugin
    return plugins
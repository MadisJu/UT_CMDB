from abc import ABC, abstractmethod
from typing import Any, Dict


class BasePlugin(ABC):
    """Base interface for all discovery plugins."""

    name: str = "base"
    description: str = "Base Plugin"

    @abstractmethod
    def discover(self, target: str) -> Dict[str, Any]:
        """single"""
        pass

    def discover_all(self, targets: list[str]) -> Dict[str, Dict[str, Any]]:
        """batch"""
        return {t: self.discover(t) for t in targets}
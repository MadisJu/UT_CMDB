from abc import ABC, abstractmethod
from typing import Any, Dict


class BasePlugin(ABC):
    name: str = "base"
    description: str = "Base Plugin"

    @abstractmethod
    def discover(self, target: str) -> Dict[str, Any]:
        pass

    def discover_all(self, targets: list[str]) -> Dict[str, Dict[str, Any]]:
        return {t: self.discover(t) for t in targets}
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseMemory(ABC):
    """Abstract base class for all memory types."""
    
    @abstractmethod
    async def retrieve(self, **kwargs) -> Dict[str, Any]:
        """Retrieve memory data."""
        pass
    
    @abstractmethod
    async def store(self, **kwargs) -> None:
        """Store memory data."""
        pass
    
    @abstractmethod
    async def clear(self, **kwargs) -> None:
        """Clear memory data."""
        pass

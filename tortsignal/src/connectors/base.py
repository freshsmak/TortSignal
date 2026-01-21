"""Base connector interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generator


class BaseConnector(ABC):
    """Abstract base class for data source connectors."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the canonical source name (e.g., 'unicourt', 'faers')."""
        ...

    @abstractmethod
    def fetch(self, **kwargs) -> Generator[dict[str, Any], None, None]:
        """
        Fetch records from the data source.
        
        Yields normalized records as dictionaries.
        Implementation should handle pagination internally.
        """
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the connector can reach its data source.
        
        Returns True if healthy, False otherwise.
        """
        ...

    def _now_utc(self) -> datetime:
        """Return current UTC datetime."""
        from datetime import timezone
        return datetime.now(timezone.utc)

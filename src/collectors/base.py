# src/collectors/base.py
from abc import ABC, abstractmethod
from typing import List
from src.analyzers.models import RawItem

class BaseCollector(ABC):
    """Abstract base class for all data collectors"""
    
    @abstractmethod
    def collect(self, keywords: List[str], limit: int = 50) -> List[RawItem]:
        """
        Collect items mentioning keywords.
        
        Args:
            keywords: List of keywords to search for
            limit: Maximum number of items to collect
            
        Returns:
            List of RawItem objects
        """
        pass

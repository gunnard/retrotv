"""Abstract base class for guide parsers."""

from abc import ABC, abstractmethod
from typing import Generator, Union, List
from pathlib import Path

from retrotv.models.guide import GuideEntry, GuideMetadata, GuideSource


class BaseGuideParser(ABC):
    """Abstract base class for guide parsers."""
    
    source_type: GuideSource
    
    @abstractmethod
    def parse(self, file_path: Path) -> Generator[GuideEntry, None, None]:
        """Parse guide file and yield entries."""
        pass
    
    @abstractmethod
    def validate(self, file_path: Path) -> bool:
        """Validate file format before parsing."""
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: Path) -> GuideMetadata:
        """Extract guide metadata."""
        pass
    
    def parse_file(self, file_path: Union[str, Path]) -> List[GuideEntry]:
        """Parse file and return list of entries."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Guide file not found: {file_path}")
        
        if not self.validate(path):
            raise ValueError(f"Invalid guide file format: {file_path}")
        
        return list(self.parse(path))

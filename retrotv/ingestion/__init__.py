"""Guide ingestion module for parsing programming guides."""

from retrotv.ingestion.normalizer import TitleNormalizer
from retrotv.ingestion.base import BaseGuideParser
from retrotv.ingestion.json_parser import JSONGuideParser
from retrotv.ingestion.xml_parser import XMLTVParser
from retrotv.ingestion.csv_parser import CSVGuideParser

__all__ = [
    "TitleNormalizer",
    "BaseGuideParser",
    "JSONGuideParser",
    "XMLTVParser",
    "CSVGuideParser",
]


def get_parser_for_file(file_path: str) -> BaseGuideParser:
    """Get appropriate parser based on file extension."""
    ext = file_path.lower().split('.')[-1]
    
    if ext == 'json':
        return JSONGuideParser()
    elif ext in ('xml', 'xmltv'):
        return XMLTVParser()
    elif ext == 'csv':
        return CSVGuideParser()
    else:
        raise ValueError(f"Unsupported file format: {ext}")

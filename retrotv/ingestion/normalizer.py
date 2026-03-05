"""Title normalization utilities for consistent matching."""

import re
from typing import Tuple, Optional


class TitleNormalizer:
    """Normalize titles for consistent matching."""
    
    REPLACEMENTS = {
        r"&": " and ",
        r"'": "",
        r'"': "",
        r"[^\w\s]": " ",
        r"\s+": " ",
    }
    
    STOP_WORDS = {"the", "a", "an"}
    
    TITLE_ALIASES = {
        "mash": "m*a*s*h",
        "m a s h": "m*a*s*h",
        "star trek the next generation": "star trek: the next generation",
        "star trek tng": "star trek: the next generation",
        "st tng": "star trek: the next generation",
        "threes company": "three's company",
        "three s company": "three's company",
        "wkrp": "wkrp in cincinnati",
        "laverne and shirley": "laverne & shirley",
        "simon and simon": "simon & simon",
    }
    
    STRIP_SUFFIXES = [
        r"\s*\(\d{4}\)$",
        r"\s*\(tv\s*movie\)$",
        r"\s*\(miniseries\)$",
        r"\s*:\s*the\s+series$",
        r"\s*\(us\)$",
        r"\s*\(uk\)$",
        r"\s*\(rerun\)$",
        r"\s*\(repeat\)$",
        r"\s*\(r\)$",
    ]
    
    @classmethod
    def normalize(cls, title: str) -> str:
        """Normalize a title for matching."""
        if not title:
            return ""
        
        result = title.lower().strip()
        
        for pattern in cls.STRIP_SUFFIXES:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)
        
        for pattern, replacement in cls.REPLACEMENTS.items():
            result = re.sub(pattern, replacement, result)
        
        result = result.strip()
        
        words = result.split()
        if words and words[0] in cls.STOP_WORDS:
            words = words[1:]
        result = " ".join(words)
        
        result = cls.TITLE_ALIASES.get(result, result)
        
        return result.strip()
    
    @classmethod
    def extract_year(cls, title: str) -> Tuple[str, Optional[int]]:
        """Extract year from title like 'Movie Title (1985)'."""
        match = re.search(r'\((\d{4})\)\s*$', title)
        if match:
            year = int(match.group(1))
            clean_title = title[:match.start()].strip()
            return clean_title, year
        return title, None
    
    @classmethod
    def extract_episode_info(cls, text: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract season and episode numbers from text."""
        patterns = [
            r"s(\d+)\s*e(\d+)",
            r"season\s*(\d+)\s*episode\s*(\d+)",
            r"(\d+)x(\d+)",
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return int(match.group(1)), int(match.group(2))
        
        return None, None
    
    @classmethod
    def clean_episode_title(cls, title: str) -> str:
        """Clean episode title for matching."""
        if not title:
            return ""
        
        result = title.lower().strip()
        result = re.sub(r'^"(.*)"$', r'\1', result)
        result = re.sub(r"^'(.*)'$", r'\1', result)
        result = re.sub(r"[^\w\s]", " ", result)
        result = re.sub(r"\s+", " ", result)
        
        return result.strip()
    
    @classmethod
    def similarity_preprocess(cls, title: str) -> str:
        """Preprocess title for similarity comparison."""
        normalized = cls.normalize(title)
        return re.sub(r"[^\w]", "", normalized)

"""Substitution data models for content replacement logic."""

from dataclasses import dataclass, field
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from retrotv.models.media import MediaItem


class SubstitutionStrategy(Enum):
    """Strategy for selecting substitutions."""
    RUNTIME_FIRST = "runtime_first"
    GENRE_FIRST = "genre_first"
    SAME_SERIES = "same_series"
    DECADE_MATCH = "decade_match"


@dataclass
class SubstitutionCandidate:
    """A potential substitution for missing content."""
    media_item: 'MediaItem'
    score: float
    runtime_score: float
    genre_score: float
    decade_score: float
    reason: str


@dataclass
class SubstitutionResult:
    """Result of substitution search for a schedule slot."""
    slot_id: str
    original_title: str
    expected_runtime_minutes: int
    expected_genres: List[str] = field(default_factory=list)
    
    candidates: List[SubstitutionCandidate] = field(default_factory=list)
    selected_candidate: Optional[SubstitutionCandidate] = None
    auto_selected: bool = False
    user_override: Optional['MediaItem'] = None
    
    @property
    def has_options(self) -> bool:
        """Check if there are substitution options."""
        return len(self.candidates) > 0
    
    @property
    def best_score(self) -> float:
        """Get the best candidate score."""
        if not self.candidates:
            return 0.0
        return max(c.score for c in self.candidates)


@dataclass
class SubstitutionRule:
    """User-defined substitution rule for persistence."""
    rule_id: str
    original_title_pattern: str
    substitute_title: str
    substitute_type: str
    priority: int = 0
    enabled: bool = True

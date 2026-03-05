"""ErsatzTV auto-mapping and deployment service."""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from retrotv.export.ersatztv_api import ErsatzTVClient, ErsatzTVConfig
from retrotv.matching.fuzzy import FuzzyMatcher
from retrotv.ingestion.normalizer import TitleNormalizer
from retrotv.models.schedule import ChannelSchedule


@dataclass
class ContentMapping:
    """A mapping between a RetroTV show title and an ErsatzTV content key."""
    show_title: str
    ersatztv_key: str
    ersatztv_name: str
    ersatztv_type: str  # "collection" or "playlist"
    confidence: float
    auto_matched: bool


@dataclass
class AutoMapResult:
    """Result of auto-mapping a schedule to ErsatzTV content."""
    mappings: List[ContentMapping] = field(default_factory=list)
    unmapped: List[str] = field(default_factory=list)
    total_shows: int = 0
    mapped_count: int = 0

    @property
    def mapping_dict(self) -> Dict[str, str]:
        """Return the mapping as a simple title->key dict for the pusher."""
        return {m.show_title: m.ersatztv_key for m in self.mappings}


def check_ersatztv_connection(url: str) -> dict:
    """Test connection to an ErsatzTV instance."""
    config = ErsatzTVConfig(url=url)
    client = ErsatzTVClient(config)
    try:
        result = client.test_connection()
        if result.get("success"):
            channels = client.get_channels()
            collections = client.get_collections()
            return {
                "success": True,
                "channels": len(channels) if isinstance(channels, list) else 0,
                "collections": len(collections) if isinstance(collections, list) else 0,
            }
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        client.close()


def fetch_ersatztv_content(url: str) -> dict:
    """Fetch all collections and playlists from ErsatzTV."""
    config = ErsatzTVConfig(url=url)
    client = ErsatzTVClient(config)
    try:
        collections = client.get_collections()
        playlists = client.get_playlists()
        return {
            "collections": collections if isinstance(collections, list) else [],
            "playlists": playlists if isinstance(playlists, list) else [],
        }
    except Exception as e:
        return {"collections": [], "playlists": [], "error": str(e)}
    finally:
        client.close()


def auto_map_schedule(
    schedule: ChannelSchedule,
    url: str,
    min_confidence: float = 70.0,
) -> AutoMapResult:
    """
    Automatically map show titles from a schedule to ErsatzTV
    collections/playlists using fuzzy matching.
    """
    show_titles = set()
    for slot in schedule.slots:
        if slot.final_item:
            title = getattr(slot.final_item, "series_title", slot.final_item.title)
            show_titles.add(title)

    result = AutoMapResult(total_shows=len(show_titles))

    if not show_titles:
        return result

    content = fetch_ersatztv_content(url)
    if not content["collections"] and not content["playlists"]:
        result.unmapped = list(show_titles)
        return result

    candidates = []
    candidate_meta = {}

    for coll in content["collections"]:
        name = coll.get("name", "")
        key = str(coll.get("id", name))
        normalized = TitleNormalizer.normalize(name)
        candidates.append(normalized)
        candidate_meta[normalized] = {
            "key": key,
            "name": name,
            "type": "collection",
        }

    for pl in content["playlists"]:
        name = pl.get("name", "")
        key = str(pl.get("id", name))
        normalized = TitleNormalizer.normalize(name)
        if normalized not in candidate_meta:
            candidates.append(normalized)
            candidate_meta[normalized] = {
                "key": key,
                "name": name,
                "type": "playlist",
            }

    for title in sorted(show_titles):
        normalized_title = TitleNormalizer.normalize(title)
        match = FuzzyMatcher.match_with_threshold(
            normalized_title, candidates, threshold=min_confidence,
        )

        if match:
            meta = candidate_meta[match.matched_string]
            result.mappings.append(ContentMapping(
                show_title=title,
                ersatztv_key=meta["key"],
                ersatztv_name=meta["name"],
                ersatztv_type=meta["type"],
                confidence=match.score,
                auto_matched=True,
            ))
            result.mapped_count += 1
        else:
            result.unmapped.append(title)

    return result


def push_schedule_to_ersatztv(
    schedule: ChannelSchedule,
    url: str,
    build_id: str,
    content_mapping: Dict[str, str],
) -> List[dict]:
    """
    Push a schedule to ErsatzTV using the Scripted Scheduling API.
    Returns a list of status dicts for each slot pushed.
    """
    from retrotv.export.ersatztv_api import ErsatzTVSchedulePusher

    config = ErsatzTVConfig(url=url)
    client = ErsatzTVClient(config)
    pusher = ErsatzTVSchedulePusher(client)

    try:
        statuses = pusher.push_schedule(schedule, build_id, content_mapping)
        return [
            {
                "current_time": s.current_time.isoformat(),
                "is_done": s.is_done,
            }
            for s in statuses
        ]
    except Exception as e:
        return [{"error": str(e)}]
    finally:
        client.close()

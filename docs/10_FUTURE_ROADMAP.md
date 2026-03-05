# 10. Non-MVP Future Roadmap

This document outlines features explicitly **NOT** included in the MVP, organized by priority and complexity.

---

## 10.1 Post-MVP Feature Categories

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        POST-MVP FEATURE ROADMAP                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  NEAR-TERM (v1.1 - v1.2)           │  MID-TERM (v1.3 - v2.0)            │
│  ─────────────────────────         │  ─────────────────────────          │
│  • Episode continuity              │  • OCR guide ingestion              │
│  • Automatic EPG generation        │  • Community channel templates      │
│  • Enhanced ad-break modeling      │  • Multi-channel networks           │
│  • Batch schedule generation       │  • Advanced AI matching             │
│                                    │                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  LONG-TERM (v2.0+)                 │  EXPERIMENTAL                       │
│  ─────────────────────────         │  ─────────────────────────          │
│  • Decade-accurate promos/ads      │  • Voice/LLM-based UI               │
│  • Smart theme-day creation        │  • Neural network matching          │
│  • Real-time schedule streaming    │  • AR TV Guide experience           │
│  • Mobile companion app            │  • Social viewing features          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10.2 Near-Term Features (v1.1 - v1.2)

### 10.2.1 Episode Continuity

**Description:** Ensure multi-episode arcs and serialized content play in correct order across schedule generation sessions.

**Scope:**
- Track last-played episode per series
- Maintain viewing history database
- Support "continue from" and "start fresh" modes
- Handle season boundaries intelligently

**Technical Approach:**
```python
@dataclass
class SeriesProgress:
    series_id: str
    last_season: int
    last_episode: int
    last_played: datetime
    total_plays: int
    
class ContinuityManager:
    def get_next_episode(self, series: Series, strategy: str = "sequential") -> Episode:
        """Get next episode based on continuity strategy."""
        # Strategies: sequential, random, shuffle_season, rewatch
        pass
    
    def mark_played(self, episode: Episode):
        """Mark episode as played, update progress."""
        pass
```

**Estimated Effort:** 2-3 weeks

---

### 10.2.2 Automatic EPG Generation

**Description:** Generate XMLTV-format EPG files from created schedules for use in TV guide applications.

**Scope:**
- Export schedule as XMLTV EPG
- Include program metadata (title, description, episode info)
- Support multiple channels in single EPG
- Periodic EPG regeneration

**Technical Approach:**
```python
class EPGGenerator:
    def generate(self, schedules: List[ChannelSchedule], days_ahead: int = 7) -> str:
        """Generate XMLTV format EPG."""
        root = ET.Element("tv")
        
        # Add channel definitions
        for schedule in schedules:
            channel = ET.SubElement(root, "channel", id=schedule.channel_name)
            ET.SubElement(channel, "display-name").text = schedule.channel_name
        
        # Add programme entries
        for schedule in schedules:
            for slot in schedule.slots:
                prog = ET.SubElement(root, "programme",
                    start=self._format_time(slot.scheduled_start),
                    stop=self._format_time(slot.scheduled_end),
                    channel=schedule.channel_name
                )
                # Add metadata...
        
        return ET.tostring(root, encoding="unicode")
```

**Estimated Effort:** 1-2 weeks

---

### 10.2.3 Enhanced Ad-Break Modeling

**Description:** Sophisticated ad-break simulation based on historical broadcast patterns.

**Scope:**
- Decade-specific ad break patterns (60s: fewer breaks, 90s: more)
- Time-of-day ad density variation
- Program-type specific breaks (drama vs sitcom vs movie)
- Network-specific commercial policies

**Technical Approach:**
```python
@dataclass
class AdBreakPattern:
    decade: str
    program_type: str
    breaks_per_hour: int
    avg_break_duration_seconds: int
    placement: List[float]  # Normalized positions (0.0 - 1.0)

class AdvancedAdCalculator:
    PATTERNS = {
        ("1970s", "sitcom"): AdBreakPattern("1970s", "sitcom", 3, 120, [0.25, 0.5, 0.75]),
        ("1980s", "sitcom"): AdBreakPattern("1980s", "sitcom", 4, 150, [0.2, 0.4, 0.6, 0.8]),
        ("1990s", "sitcom"): AdBreakPattern("1990s", "sitcom", 5, 180, [0.15, 0.3, 0.5, 0.7, 0.85]),
    }
    
    def calculate_breaks(self, slot: ScheduleSlot, decade: str) -> List[AdBreak]:
        """Calculate realistic ad breaks for a slot."""
        pass
```

**Estimated Effort:** 2 weeks

---

### 10.2.4 Batch Schedule Generation

**Description:** Generate multiple days/weeks of schedules at once with variation.

**Scope:**
- Week-at-a-time generation
- Day-of-week programming variation
- Avoid episode repetition within batch
- Preview and bulk approval

**Estimated Effort:** 1-2 weeks

---

## 10.3 Mid-Term Features (v1.3 - v2.0)

### 10.3.1 OCR Guide Ingestion

**Description:** Extract programming data from scanned TV Guide magazine pages using OCR.

**Scope:**
- Image preprocessing for scan quality
- OCR with Tesseract or cloud services
- Layout detection (grid format)
- Time/title extraction and parsing
- Confidence scoring and manual correction UI

**Technical Approach:**
```python
class TVGuideOCR:
    def __init__(self, ocr_engine: str = "tesseract"):
        self.engine = ocr_engine
    
    def process_scan(self, image_path: Path) -> List[GuideEntry]:
        """Process scanned TV Guide page."""
        # 1. Preprocess image
        processed = self._preprocess(image_path)
        
        # 2. Detect grid layout
        grid = self._detect_grid(processed)
        
        # 3. Extract cells
        cells = self._extract_cells(grid)
        
        # 4. OCR each cell
        raw_text = [self._ocr_cell(cell) for cell in cells]
        
        # 5. Parse into structured data
        entries = self._parse_entries(raw_text, grid.time_column)
        
        return entries
    
    def _preprocess(self, image_path: Path) -> np.ndarray:
        """Deskew, denoise, enhance contrast."""
        pass
    
    def _detect_grid(self, image: np.ndarray) -> GridLayout:
        """Detect time column and channel rows."""
        pass
```

**Dependencies:**
- Tesseract OCR or Google Vision API
- OpenCV for image processing
- Layout detection model (potentially custom-trained)

**Estimated Effort:** 4-6 weeks

---

### 10.3.2 Community Channel Templates

**Description:** Share and discover pre-made channel configurations created by the community.

**Scope:**
- Template format specification
- Public template repository
- Browse/search templates
- One-click import
- Rating and review system
- Template versioning

**Technical Approach:**
```python
@dataclass
class ChannelTemplate:
    id: str
    name: str
    description: str
    author: str
    decade: str
    channel_type: str  # "network_recreation", "theme_channel", "marathon"
    guide_data: List[TemplateSlot]
    tags: List[str]
    downloads: int
    rating: float

class TemplateRepository:
    API_URL = "https://api.retrotv-templates.com"
    
    async def search(self, query: str, decade: str = None) -> List[ChannelTemplate]:
        """Search community templates."""
        pass
    
    async def download(self, template_id: str) -> ChannelTemplate:
        """Download a template."""
        pass
    
    async def publish(self, template: ChannelTemplate) -> str:
        """Publish a template to the community."""
        pass
```

**Estimated Effort:** 4-5 weeks (including backend service)

---

### 10.3.3 Multi-Channel Network Generation

**Description:** Generate coordinated schedules across multiple channels simulating a broadcast network.

**Scope:**
- Network-level configuration (NBC, CBS, ABC packages)
- Cross-channel programming rules
- Synchronized prime-time blocks
- Network-wide substitution pools
- Unified EPG output

**Technical Approach:**
```python
@dataclass
class NetworkConfig:
    name: str
    channels: List[ChannelConfig]
    shared_library_rules: dict
    prime_time_sync: bool
    cross_promotion: bool

class NetworkScheduleGenerator:
    def generate_network(
        self, 
        config: NetworkConfig,
        guides: Dict[str, List[GuideEntry]]
    ) -> Dict[str, ChannelSchedule]:
        """Generate coordinated schedules for entire network."""
        schedules = {}
        
        # Phase 1: Generate individual schedules
        for channel_config in config.channels:
            guide = guides[channel_config.name]
            schedules[channel_config.name] = self._generate_channel(guide)
        
        # Phase 2: Coordinate across network
        if config.prime_time_sync:
            self._sync_prime_time(schedules)
        
        # Phase 3: Apply cross-channel rules
        self._apply_network_rules(schedules, config)
        
        return schedules
```

**Estimated Effort:** 3-4 weeks

---

### 10.3.4 Advanced AI-Based Metadata Reconciliation

**Description:** Use LLMs/AI to improve matching accuracy and resolve ambiguous cases.

**Scope:**
- LLM-assisted title disambiguation
- Episode identification from descriptions
- Era-appropriate content suggestions
- Natural language query for library search
- Automatic alias database building

**Technical Approach:**
```python
class AIMetadataReconciler:
    def __init__(self, model: str = "gpt-4"):
        self.client = OpenAI()
        self.model = model
    
    async def disambiguate_title(
        self, 
        guide_title: str,
        candidates: List[Series],
        context: str
    ) -> Series:
        """Use LLM to pick best match when fuzzy matching is uncertain."""
        prompt = f"""
        Historical TV guide lists: "{guide_title}"
        
        Possible matches in library:
        {self._format_candidates(candidates)}
        
        Context: {context}
        
        Which is the correct match? Respond with the index number only.
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        index = int(response.choices[0].message.content.strip())
        return candidates[index]
    
    async def identify_episode(
        self,
        series: Series,
        episode_description: str
    ) -> Optional[Episode]:
        """Identify episode from description using AI."""
        pass
```

**Estimated Effort:** 3-4 weeks

---

## 10.4 Long-Term Features (v2.0+)

### 10.4.1 Decade-Accurate Promo/Ad Insertion

**Description:** Insert authentic-feeling commercial breaks, station IDs, and promos from the appropriate era.

**Scope:**
- Curated vintage commercial database integration
- Era-appropriate station ID generation
- "Coming up next" bumper generation
- Time-of-day appropriate ad selection
- Ad category balancing (car, food, household, etc.)

**Estimated Effort:** 6-8 weeks

---

### 10.4.2 Smart Theme-Day Creation

**Description:** Automatically generate themed programming blocks (Christmas episodes, Halloween specials, etc.).

**Scope:**
- Holiday episode detection in library
- Theme tag database
- Actor/director spotlights
- "Best of" compilation generation
- Marathon mode

**Technical Approach:**
```python
class ThemeDayGenerator:
    THEMES = {
        "christmas": {
            "keywords": ["christmas", "xmas", "holiday", "santa"],
            "date_hints": ["12-24", "12-25"],
            "episode_patterns": [r"christmas", r"holiday"]
        },
        "halloween": {
            "keywords": ["halloween", "scary", "spooky", "haunted"],
            "date_hints": ["10-31"],
            "episode_patterns": [r"halloween", r"trick.or.treat"]
        }
    }
    
    def generate_theme_day(
        self, 
        library: MediaLibrary,
        theme: str,
        duration_hours: int = 24
    ) -> ChannelSchedule:
        """Generate a themed programming day."""
        pass
```

**Estimated Effort:** 4-5 weeks

---

### 10.4.3 Real-Time Schedule Streaming

**Description:** Stream schedule data in real-time, allowing dynamic updates and live-like experience.

**Scope:**
- WebSocket schedule streaming
- "What's on now" real-time display
- Schedule synchronization across devices
- Live schedule adjustments
- "Join in progress" support

**Estimated Effort:** 4-6 weeks

---

### 10.4.4 Mobile Companion App

**Description:** Mobile app for browsing schedules, managing recordings, and remote control.

**Scope:**
- iOS and Android apps (React Native or Flutter)
- Browse schedules
- Push notifications ("Your show is starting")
- Remote schedule management
- Quick substitution approval

**Estimated Effort:** 8-12 weeks

---

## 10.5 Experimental Features

### 10.5.1 Voice/LLM-Based UI

**Description:** Natural language interface for schedule creation and management.

**Example Interactions:**
```
User: "Create a 1985 NBC Thursday night lineup"
AI: "I found a Thursday schedule from March 1985. It includes The Cosby Show, 
     Family Ties, Cheers, Night Court, and Hill Street Blues. 
     I matched 4 of 5 shows in your library. Should I create this schedule?"

User: "Replace Night Court with something similar from that era"
AI: "I suggest 'Taxi' - it's also a workplace comedy from the early 80s 
     with similar runtime. Would you like me to make this substitution?"
```

**Technical Approach:**
- Function calling with structured outputs
- Intent classification
- Conversational state management
- Action confirmation flow

**Estimated Effort:** 6-8 weeks

---

### 10.5.2 Neural Network Matching

**Description:** Train custom models for title matching and content similarity.

**Scope:**
- Embeddings-based title matching
- Content similarity from descriptions
- Visual similarity for thumbnails
- Transfer learning from media databases

**Estimated Effort:** 8-12 weeks

---

## 10.6 Feature Prioritization Matrix

| Feature | User Value | Technical Complexity | Dependencies | Priority Score |
|---------|------------|---------------------|--------------|----------------|
| Episode Continuity | High | Low | None | **9/10** |
| Automatic EPG | High | Low | None | **9/10** |
| Enhanced Ad Breaks | Medium | Medium | None | 7/10 |
| Batch Generation | Medium | Low | None | 7/10 |
| OCR Ingestion | High | High | External OCR | 6/10 |
| Community Templates | High | Medium | Backend infra | 6/10 |
| Multi-Channel | Medium | Medium | None | 6/10 |
| AI Matching | Medium | High | LLM API | 5/10 |
| Decade Promos | Medium | High | Content library | 4/10 |
| Theme Days | Medium | Medium | Episode tagging | 5/10 |
| Voice UI | Low | High | LLM API | 3/10 |

---

## 10.7 Version Roadmap Summary

### v1.1 (3-4 months post-MVP)
- Episode continuity tracking
- Automatic EPG generation
- Batch schedule generation
- UI polish and bug fixes

### v1.2 (6 months post-MVP)
- Enhanced ad-break modeling
- Improved matching algorithms
- Performance optimizations
- Additional export formats

### v1.3 (9 months post-MVP)
- Community template system (basic)
- Multi-channel support
- OCR ingestion (beta)

### v2.0 (12-18 months post-MVP)
- AI-assisted matching
- Full community features
- Theme day generation
- Mobile companion app (beta)

---

## 10.8 Contributing to Future Features

Future contributors should:
1. Review this roadmap before proposing new features
2. Check if proposed feature fits within defined scope
3. Consider MVP stability before adding complexity
4. Propose features via GitHub Issues with:
   - Use case description
   - Technical approach outline
   - Estimated effort
   - Dependencies

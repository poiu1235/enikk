"""Screenshot state: raw image + UI parser results."""
from dataclasses import dataclass, field

@dataclass
class GameState:
    """Holds a screenshot and its structured UI analysis."""
    image_b64: str = ""
    width: int = 0
    height: int = 0
    ocr: list = field(default_factory=list)
    bbox_desc: str = ""
    timestamp: str = ""

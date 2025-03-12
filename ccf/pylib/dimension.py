from dataclasses import dataclass


@dataclass(eq=False)
class Dimension:
    dim: str = None
    units: str = None
    min: float = None
    low: float = None
    high: float = None
    max: float = None
    start: int = None
    end: int = None

from dataclasses import dataclass


@dataclass(eq=False)
class Dimension:
    dim: str | None = None
    units: str | None = None
    min: float | None = None
    low: float | None = None
    high: float | None = None
    max: float | None = None

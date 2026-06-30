from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from esg_monthly_agent.graph import build_graph

graph = build_graph()

__all__ = ["graph"]

from __future__ import annotations

import pytest

from esg_monthly_agent.skills.research_execution.fetch_and_parse.runner import fetch


@pytest.mark.parametrize("mode", ["web", "hosted_web", "deep_research"])
def test_source_mode_blocks_fetch(mode):
    with pytest.raises(RuntimeError, match="fetch_pages is blocked"):
        fetch({"research_mode": mode})

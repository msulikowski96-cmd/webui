"""
Regression test for issue #58:
    install_skill auto-discovery fails to find nested skills when given a root directory.

Before the fix, the discovery used a shallow directory listing that only found
SKILL.md files in the immediate children of the target path.  Skills nested deeper
(e.g. plugins/visual-explainer/SKILL.md) were silently skipped.

The fix replaced the shallow scan with GitHub's recursive Git Trees API
(GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1), which returns every
file in the repository in a single call and therefore catches any depth of nesting.

These tests mock the GitHub API response and verify that the recursive discovery
logic handles both shallow and deeply-nested SKILL.md paths correctly.
"""

import asyncio
import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# ---------------------------------------------------------------------------
# Load the skills manager module without importing OpenWebUI dependencies
# ---------------------------------------------------------------------------
MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "plugins"
    / "tools"
    / "openwebui-skills-manager"
    / "openwebui_skills_manager.py"
)

_spec = importlib.util.spec_from_file_location("openwebui_skills_manager", MODULE_PATH)
_mod = importlib.util.module_from_spec(_spec)
# Stub out open_webui imports so the module loads in a plain Python environment
sys.modules.setdefault(
    "open_webui.models.skills",
    types.ModuleType("open_webui.models.skills"),
)
sys.modules.setdefault(
    "open_webui",
    types.ModuleType("open_webui"),
)
sys.modules.setdefault(
    "open_webui.models",
    types.ModuleType("open_webui.models"),
)
_spec.loader.exec_module(_mod)

_discover = _mod._discover_skills_from_github_directory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_valves(trusted="github.com,raw.githubusercontent.com,api.github.com"):
    """Return a minimal valves-like object accepted by the skills manager helpers."""
    return types.SimpleNamespace(
        TRUSTED_DOMAINS=trusted,
        INSTALL_FETCH_TIMEOUT=12.0,
        SHOW_STATUS=False,
    )


def _api_tree_response(paths):
    """Build a fake GitHub Git Trees API JSON payload for the given file paths."""
    return json.dumps(
        {
            "tree": [
                {"path": p, "type": "blob"}
                for p in paths
            ]
        }
    ).encode("utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_discovers_top_level_skill():
    """A SKILL.md directly in the target path is discovered."""
    valves = _make_valves()
    url = "https://github.com/owner/repo/tree/main/skills"

    fake_tree = _api_tree_response(["skills/SKILL.md"])

    with patch.object(_mod, "_fetch_bytes", new=AsyncMock(return_value=fake_tree)):
        result = await _discover(valves, url, "en-US")

    assert result == ["https://github.com/owner/repo/tree/main/skills"]


@pytest.mark.asyncio
async def test_discovers_single_nested_skill():
    """A SKILL.md one level below the target path is discovered (issue #58 scenario)."""
    valves = _make_valves()
    url = "https://github.com/owner/repo/tree/main/plugins"

    fake_tree = _api_tree_response(["plugins/visual-explainer/SKILL.md"])

    with patch.object(_mod, "_fetch_bytes", new=AsyncMock(return_value=fake_tree)):
        result = await _discover(valves, url, "en-US")

    assert result == ["https://github.com/owner/repo/tree/main/plugins/visual-explainer"]


@pytest.mark.asyncio
async def test_discovers_deeply_nested_skill():
    """A SKILL.md arbitrarily deep below the target path is discovered."""
    valves = _make_valves()
    url = "https://github.com/owner/repo/tree/main"

    fake_tree = _api_tree_response(
        ["deep/nested/path/to/my-skill/SKILL.md"]
    )

    with patch.object(_mod, "_fetch_bytes", new=AsyncMock(return_value=fake_tree)):
        result = await _discover(valves, url, "en-US")

    assert result == [
        "https://github.com/owner/repo/tree/main/deep/nested/path/to/my-skill"
    ]


@pytest.mark.asyncio
async def test_discovers_multiple_skills_at_various_depths():
    """Multiple SKILL.md files at different depths are all discovered (regression for #58)."""
    valves = _make_valves()
    url = "https://github.com/owner/repo/tree/main/plugins"

    paths = [
        "plugins/alpha/SKILL.md",
        "plugins/beta/v2/SKILL.md",
        "plugins/gamma/sub/deep/SKILL.md",
        # Should be excluded – not inside target_path
        "other/delta/SKILL.md",
    ]
    fake_tree = _api_tree_response(paths)

    with patch.object(_mod, "_fetch_bytes", new=AsyncMock(return_value=fake_tree)):
        result = await _discover(valves, url, "en-US")

    assert "https://github.com/owner/repo/tree/main/plugins/alpha" in result
    assert "https://github.com/owner/repo/tree/main/plugins/beta/v2" in result
    assert "https://github.com/owner/repo/tree/main/plugins/gamma/sub/deep" in result
    # Must NOT include skills outside the requested path
    assert not any("other/delta" in r for r in result)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_excludes_skills_outside_target_path():
    """Skills that are not under the target path are filtered out."""
    valves = _make_valves()
    url = "https://github.com/owner/repo/tree/main/skills"

    fake_tree = _api_tree_response(
        [
            "skills/foo/SKILL.md",
            "unrelated/bar/SKILL.md",  # outside target
        ]
    )

    with patch.object(_mod, "_fetch_bytes", new=AsyncMock(return_value=fake_tree)):
        result = await _discover(valves, url, "en-US")

    assert len(result) == 1
    assert "skills/foo" in result[0]
    assert not any("unrelated" in r for r in result)


@pytest.mark.asyncio
async def test_returns_empty_list_when_no_skill_md_found():
    """Returns an empty list when the tree contains no SKILL.md files."""
    valves = _make_valves()
    url = "https://github.com/owner/repo/tree/main/empty"

    fake_tree = _api_tree_response(["empty/README.md", "empty/src/main.py"])

    with patch.object(_mod, "_fetch_bytes", new=AsyncMock(return_value=fake_tree)):
        result = await _discover(valves, url, "en-US")

    assert result == []


@pytest.mark.asyncio
async def test_deduplicates_skill_urls():
    """Each skill directory URL appears at most once even if multiple files match."""
    valves = _make_valves()
    url = "https://github.com/owner/repo/tree/main/skills"

    # Two entries that resolve to the same directory should not produce duplicates.
    fake_tree = _api_tree_response(
        [
            "skills/foo/SKILL.md",
            "skills/foo/SKILL.md",  # exact duplicate path in API response
        ]
    )

    with patch.object(_mod, "_fetch_bytes", new=AsyncMock(return_value=fake_tree)):
        result = await _discover(valves, url, "en-US")

    assert len(result) == 1


@pytest.mark.asyncio
async def test_returns_empty_list_on_fetch_error():
    """Returns an empty list (does not raise) when the GitHub API call fails."""
    valves = _make_valves()
    url = "https://github.com/owner/repo/tree/main/skills"

    with patch.object(_mod, "_fetch_bytes", new=AsyncMock(side_effect=Exception("network error"))):
        result = await _discover(valves, url, "en-US")

    assert result == []


@pytest.mark.asyncio
async def test_uses_recursive_api_url():
    """Verifies that the recursive=1 Git Trees API endpoint is used (not a shallow listing)."""
    valves = _make_valves()
    url = "https://github.com/myorg/myrepo/tree/develop/plugins"

    captured_urls = []

    async def fake_fetch(v, u):
        captured_urls.append(u)
        return _api_tree_response([])

    with patch.object(_mod, "_fetch_bytes", new=fake_fetch):
        await _discover(valves, url, "en-US")

    assert len(captured_urls) == 1
    fetched = captured_urls[0]
    assert "api.github.com" in fetched
    assert "myorg" in fetched
    assert "myrepo" in fetched
    assert "recursive=1" in fetched

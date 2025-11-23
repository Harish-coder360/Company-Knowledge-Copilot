"""Lightweight MCP client placeholder.

This module demonstrates how the app would connect to an MCP server. For the sample
project we treat `MCP_SERVER_CONFIG` as a path to a folder containing synced assets
(e.g., output from a GitHub MCP server that materializes README/docs locally).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)


class MCPClient:
    """Minimal file-backed MCP client."""

    def __init__(self, config_path: str | None = None) -> None:
        path = config_path or settings.mcp_server_config
        self.config_path = Path(path) if path else None
        if not self.config_path:
            logger.warning("MCP server config not provided; MCP features are disabled")

    def list_assets(self) -> List[Path]:
        if not self.config_path or not self.config_path.exists():
            return []
        return [p for p in self.config_path.rglob("*") if p.is_file()]

    def fetch_markdown_assets(self) -> List[Tuple[str, str]]:
        """Return markdown/text assets to feed into the ingest pipeline."""

        assets: List[Tuple[str, str]] = []
        for path in self.list_assets():
            if path.suffix.lower() not in {".md", ".txt"}:
                continue
            try:
                assets.append((path.name, path.read_text(encoding="utf-8")))
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed reading MCP asset %s: %s", path, exc)
        return assets

    def sync_github_repo(self, repo_url: str) -> List[Tuple[str, str]]:
        """Placeholder GitHub sync using local MCP mirror.

        In a real deployment this would call an MCP GitHub server to fetch README and
        docs from the repository. Here we reuse `fetch_markdown_assets` so the data
        flow stays consistent for testing/demo purposes.
        """

        logger.info("Syncing repository via MCP mirror: %s", repo_url)
        return self.fetch_markdown_assets()

"""Load the TOML configuration file."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import datetime, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_FOLDERS = {
    "chatgpt": "ChatGPT",
    "claude": "Claude",
    "claude-code": "Claude Code",
    "codex": "Codex",
}


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    vault_path: Path
    root_folder: str
    timezone: tzinfo
    folders: dict[str, str]
    claude_code_dir: Path
    codex_dir: Path

    @property
    def import_root(self) -> Path:
        return self.vault_path / self.root_folder


def load_config(path: Path) -> Config:
    if not path.is_file():
        raise ConfigError(f"Config file not found: {path} (copy tkn.example.toml to tkn.toml)")
    with path.open("rb") as f:
        data = tomllib.load(f)

    vault = data.get("vault_path")
    if not vault:
        raise ConfigError("vault_path is required")
    vault_path = Path(vault).expanduser()
    if not vault_path.is_dir():
        raise ConfigError(f"vault_path does not exist: {vault_path}")

    root_folder = data.get("root_folder")
    if not root_folder:
        raise ConfigError("root_folder is required")

    tz_name = data.get("timezone") or ""
    try:
        timezone = ZoneInfo(tz_name) if tz_name else _local_timezone()
    except Exception as exc:
        raise ConfigError(f"Unknown timezone: {tz_name}") from exc

    # TOML keys use underscores; source names use hyphens.
    folders = dict(DEFAULT_FOLDERS)
    for key, value in (data.get("folders") or {}).items():
        folders[key.replace("_", "-")] = str(value)

    sources = data.get("sources") or {}
    home = Path.home()
    return Config(
        vault_path=vault_path,
        root_folder=root_folder,
        timezone=timezone,
        folders=folders,
        claude_code_dir=_dir_or_default(sources.get("claude_code_dir"), home / ".claude" / "projects"),
        codex_dir=_dir_or_default(sources.get("codex_dir"), home / ".codex" / "sessions"),
    )


def _dir_or_default(value: str | None, default: Path) -> Path:
    return Path(value).expanduser() if value else default


def _local_timezone() -> tzinfo:
    tz = datetime.now().astimezone().tzinfo
    assert tz is not None
    return tz

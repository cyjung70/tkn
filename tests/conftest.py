from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from tkn.config import DEFAULT_FOLDERS, Config

FIXTURES = Path(__file__).parent / "fixtures"
ROOT_FOLDER = "Imported"


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    path = tmp_path / "vault"
    path.mkdir()
    return path


@pytest.fixture
def config(vault: Path) -> Config:
    return Config(
        vault_path=vault,
        root_folder=ROOT_FOLDER,
        timezone=ZoneInfo("Asia/Seoul"),
        folders=dict(DEFAULT_FOLDERS),
        claude_code_dir=FIXTURES / "claude_code",
        codex_dir=FIXTURES / "codex",
    )


@pytest.fixture
def config_file(tmp_path: Path, vault: Path) -> Path:
    path = tmp_path / "tkn.toml"
    path.write_text(
        f"vault_path = {str(vault)!r}\n"
        f'root_folder = "{ROOT_FOLDER}"\n'
        'timezone = "Asia/Seoul"\n'
        "[sources]\n"
        f"claude_code_dir = {str(FIXTURES / 'claude_code')!r}\n"
        f"codex_dir = {str(FIXTURES / 'codex')!r}\n",
        encoding="utf-8",
    )
    return path

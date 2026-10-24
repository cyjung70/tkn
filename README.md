# TKN — TonaBIT Knowledge Nexus

**Separate Sources, Connect Knowledge.**

Imports conversation histories from ChatGPT, Claude, Claude Code, and Codex into an Obsidian vault, one Markdown note per conversation. Original records are kept separately per tool, with provenance and timestamps, and are never overwritten.

## Setup

Requires Python 3.11+.

```powershell
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
copy tkn.example.toml tkn.toml   # then set vault_path
```

## Usage

```powershell
tkn import chatgpt  path\to\chatgpt-export.zip
tkn import claude   path\to\claude-export.zip
tkn import claude-code
tkn import codex
```

Options: `--dry-run`, `--since YYYY-MM-DD`, `-v` (list created notes), `--config PATH`.

Conversations that already exist in the vault (matched by `source` + `id` in the frontmatter) are skipped, so re-running is safe and never overwrites your edits.

### Privacy

Exports, session logs, `tkn.toml`, and vault output are gitignored. Never commit real conversations.

## Folder structure

Notes are written to `<vault>/<root_folder>/<Tool>/<YYYY-MM>/<YYYY-MM-DD>_<title>.md`.

```
tkn/          # importers, vault writer, CLI
tests/        # synthetic fixtures only
scripts/      # Claude export helper scripts
docs/         # planning documents and earlier README
```

## Roadmap

v0.1 (conversation import) is implemented. Next: topic classification, then the Harness pipeline toward TKN 1.0.

Planning documents:
- `docs/TKN_Requirements.md`: product scope and TKN 1.0 requirements
- `docs/TKN_Harness_Architecture.md`: iterative automation pipeline and three human approval gates
- `docs/Claude_Code_Instructions.md`: English instructions to analyze the existing project before coding

Review the plan before authorizing code changes.

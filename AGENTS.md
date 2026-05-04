# AGENTS.md — LucidShark Development

## Dev Environment Setup

```bash
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .          # Installs in editable mode, registers all entry points
```

## Building the Binary

```bash
pyinstaller lucidshark.spec --clean
./dist/lucidshark --version   # Verify it built
```

Binary lands at `dist/lucidshark`. Always use `./dist/lucidshark` (or `./lucidshark` after install) to test the binary, not `python -m`.

## Version Source of Truth

- **Binary/package distribution**: `src/lucidshark/__init__.__version__` (currently 0.7.6)
- `pyproject.toml` version is `0.0.0-dev` — this is intentionally wrong for development and must not be relied upon

## Running Tests

```bash
# Unit tests only (default — ignores slow/integration suites)
pytest tests/unit -v

# Single test file
pytest tests/unit/core/test_git.py -v

# Integration tests (require external language toolchains)
pytest tests/integration/projects -v
```

Pytest config (`pyproject.toml`):
- `asyncio_mode = "auto"` — async tests Just Work
- `addopts` excludes: `tests/integration/projects`, `tests/integration/scanners`, and the python-webapp/typescript-api internal test dirs
- **Telemetry is disabled in all tests** via `tests/conftest.py`: `LUCIDSHARK_TELEMETRY=0`

## Running LucidShark Against Itself

```bash
# Build binary first, then scan
pyinstaller lucidshark.spec --clean
./dist/lucidshark scan --all --all-files --format summary

# Or after pip install -e .:
lucidshark scan --all --all-files --format summary
```

CI runs this on both `ubuntu-latest` and `macos-latest` on every push.

## Code Structure

- **Entry point**: `src/lucidshark/cli/__init__.py` → `CLIRunner.run()`
- **Source root**: `src/lucidshark/`
- **Plugin entry points** are defined in `pyproject.toml` (`[project.entry-points."lucidshark.<type>"]`) — linters, scanners, reporters, type_checkers, test_runners, coverage, formatters, duplication
- **CLI commands**: `src/lucidshark/cli/commands/{scan,init,serve,doctor,validate,overview,status,help}.py`

## Auto-Downloaded Tools

Tools are downloaded automatically to `{project}/.lucidshark/bin/`. Their versions are pinned in `pyproject.toml` under `[tool.lucidshark.tools]`:

```toml
[tool.lucidshark.tools]
trivy = "0.69.3"
opengrep = "1.16.5"
checkov = "3.2.513"
gosec = "2.25.0"
pmd = "7.23.0"
checkstyle = "13.3.0"
spotbugs = "4.9.8"
ktlint = "1.8.0"
detekt = "1.23.8"
duplo = "0.2.0"
```

For language tools (ruff, eslint, mypy, etc.), LucidShark uses whatever is installed in the environment — it does NOT manage those versions.

## Incremental Scanning (Default Behavior)

**Scans only changed files by default** (uncommitted changes). Use `--all-files` for full project scans:
```bash
./lucidshark scan --all --all-files   # Full scan
./lucidshark scan --linting           # Changed files only (default)
```

`--base-branch` filters results to files changed since a branch (full analysis runs; only reporting is filtered).

## Strict Mode

LucidShark runs in strict mode by default (`settings.strict_mode: true`): every configured tool must run successfully. A missing or failing tool causes a HIGH-severity issue and scan failure. This is configurable per-tool via `mandatory: false`.

## Quality Overview

```bash
./lucidshark scan --all --all-files                          # Must run full scan first
./lucidshark overview --update                               # Generates QUALITY.md
```

The overview reads cached results from `.lucidshark/last-scan.json`. **It will reject partial/incremental scans** — the scan must have used `--all-files`.

## Release Process

Releases are tagged (`v*`) and built via `.github/workflows/release.yml`:
1. Quality gate: LucidShark scans itself on Python 3.10, 3.11, 3.12 across Ubuntu + macOS
2. Binary builds: Linux (glibc 2.31/Debian 11 for compatibility), macOS (Intel + ARM)
3. GitHub Release is created with all 4 binaries attached

**Linux builds run in a Debian 11 container** (`python:3.11-slim-bullseye`) to avoid glibc 2.38+ requirements from newer Ubuntu.

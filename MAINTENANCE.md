# `doppelt_so_clever` — Update List

**Priority: LOW.** This repo is already at portfolio standard. Listed cleanup items are minor polish, not blockers. Only address if other repos are done.

## Minor cleanup

- [ ] **Remove committed `.coverage` file** from the repo. Add to `.gitignore` if not already.
- [ ] **Verify `__pycache__/` is gitignored** (it appears on disk but seems excluded from git — confirm).
- [ ] **Remove `doppelt_so_clever.egg-info/`** from disk if not gitignored.

## Modernisation (optional but high signal)

- [ ] **Migrate `setup.py` → `pyproject.toml`** (PEP 621). Current setup is functional but reads as ~2022 stack.
- [ ] **Switch pylint+flake8 → ruff.** One tool, ~100× faster, modern default. Update Makefile and CI accordingly.
- [ ] **Add type checking to CI** (`mypy` or `pyright`). You have rich type hints in the dataclass configs; might as well enforce them.
- [ ] **Add a lockfile** (`uv.lock` via `uv`, or `requirements.lock` via pip-tools). Pinned-range deps in `setup.py` aren't reproducible builds.
- [ ] **CI matrix** — run tests on Python 3.10, 3.11, 3.12 to back the `python_requires=">=3.10"` claim.
- [ ] **Cache `.venv` between CI runs** to speed up the workflow.

## Nice to have

- [ ] **Split CI into parallel jobs** (lint, test, RL-gate) instead of sequential.
- [ ] **Add Dependabot config** for security/version updates.
- [ ] **Add a CONTRIBUTING.md** documenting the "no docstrings, one assert per test" conventions for outside readers.
- [ ] **Add a CHANGELOG.md.**

## What this fixes in the portfolio narrative

Before: "polished but tooling reads as 2022"
After: "polished and tooling reflects current 2026 stack"

This repo carries the polish-showcase pin slot. It doesn't need to be perfect — just current.

## Estimated effort

Minor cleanup: 30 minutes. Modernisation block: ~1 day. Skip if `synapse_sdk` and `autibot` aren't done yet.

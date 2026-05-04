---
description: Review generated code for style and quality compliance before finishing a task
auto_execution_mode: 3
---

Run through this checklist on all generated/modified code:

1. **No comments or docstrings** — Remove any comments, inline comments, and docstrings from generated code.

2. **No file-level pylint disables** — If pylint reports an issue, fix the root cause instead of adding `# pylint: disable=...` at file level. For example, move pytest fixtures to `conftest.py` to avoid `redefined-outer-name`.

3. **Small methods** — If any method is longer than ~15 lines, split it into smaller private helpers.

4. **Reduce repetition** — Look for methods that follow the same pattern with different parameters. Consolidate them into a single parameterized method.

5. **One assert per test** — Each test method should contain exactly one `assert` statement. Split multi-assert tests into separate test methods grouped by test class.

6. **Run lint** — Run `make lint` using the virtual environment and iterate until:
   - call `git add` all modified files
   - pylint reports 10.00/10
   - No additional warnings or errors are listed
   - flake8 reports 0 issues

7. **Run tests** — Run `python -m pytest` using the virtual environment and confirm all tests pass.

8. **Update documentation** — Check that all documentation files in the repository (`README.md`, `ARCHITECTURE.md`, `RULES.md`, `TODO.md`, `RL_PLAN.md`, etc.) reflect the current state of the codebase. Update any sections that are outdated due to changes made in this task.

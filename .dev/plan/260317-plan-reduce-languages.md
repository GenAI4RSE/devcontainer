# Reduce Supported Languages Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update all code, tests, and docs to reflect that only `python` and `node` are supported languages, with default versions changed to `"latest"`.

**Architecture:** The language fragments are already staged (4 deleted, 2 modified). This plan updates all downstream references: test assertions, batch counts (36→12), CLI help text, CLAUDE.md, README.md, and spec/plan docs.

**Tech Stack:** Python, pytest, click, ruff

---

## Summary of Changes

- **Languages:** 6 → 2 (`python`, `node`), both with `_default_version: "latest"`
- **Batch count:** 36 → 12 (2 languages × 6 agent options)
- **Removed:** `rust`, `r`, `julia`, `c-cpp-fortran`

## Files to Modify

| File | What Changes |
|------|-------------|
| `tests/test_dimensions.py` | Language count 6→2, ID set |
| `tests/test_generator.py` | Remove rust/c-cpp-fortran refs, batch 36→12 |
| `tests/test_cli.py` | Remove rust refs, batch 36→12, list assertions |
| `tests/test_validator.py` | Replace `"rust"` with `"node"` in batch fixture |
| `src/devcc/cli.py` | Batch help text 6→2, 36→12, remove rust example |
| `CLAUDE.md` | Batch count 36→12 |
| `README.md` | Language table, examples |
| `.dev/spec/260317-spec-devcc-package.md` | Language table, counts, examples |

---

### Task 1: Update Tests

**Files:**
- Modify: `tests/test_dimensions.py`
- Modify: `tests/test_generator.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_validator.py`

- [ ] **Step 1: Update test_dimensions.py**

Change `test_list_available_languages`:
```python
# OLD
assert len(langs) == 6
ids = {f["_id"] for f in langs}
assert ids == {"python", "node", "rust", "r", "julia", "c-cpp-fortran"}

# NEW
assert len(langs) == 2
ids = {f["_id"] for f in langs}
assert ids == {"python", "node"}
```

- [ ] **Step 2: Update test_generator.py**

1. In `TestResolveCustomKeys.test_extra_apt_packages_appended`, replace `c-cpp-fortran` fixture with a generic one that still tests the feature:
```python
# OLD
lang_frags = [
    {
        "_id": "c-cpp-fortran",
        "_name": "C",
        ...
    }
]

# NEW — keep the test logic, just change the ID/name
lang_frags = [
    {
        "_id": "test-lang",
        "_name": "Test",
        "_extra_apt_packages": ["gcc", "gdb"],
        "_default_version": "latest",
        "_feature_key": "x",
        "_version_param": "version",
    }
]
```

2. In `TestGenerate.test_no_agent`, change `rust` to `node`:
```python
# OLD
generate([("rust", None)], [], tmp_output)
assert data["name"] == "Rust"

# NEW
generate([("node", None)], [], tmp_output)
assert data["name"] == "TypeScript / Node.js"
```

3. In `TestGenerateBatch`:
```python
# OLD
assert len(paths) == 36
...
assert (tmp_output / "c-cpp-fortran-codex").exists()

# NEW
assert len(paths) == 12
...
assert (tmp_output / "node-codex").exists()
```

- [ ] **Step 3: Update test_cli.py**

1. In `TestCreate.test_no_agent`, change `rust` to `node`:
```python
# OLD
result = runner.invoke(main, ["create", "-l", "rust", "-o", str(out)])
assert data["name"] == "Rust"

# NEW
result = runner.invoke(main, ["create", "-l", "node", "-o", str(out)])
assert data["name"] == "TypeScript / Node.js"
```

2. In `TestBatch.test_generates_36_templates`:
```python
# OLD
assert len(dirs) == 36

# NEW
assert len(dirs) == 12
```

3. In `TestList.test_lists_all_languages_and_agents`, remove deleted language assertions:
```python
# REMOVE these lines:
assert "rust" in result.output
assert "julia" in result.output
assert "c-cpp-fortran" in result.output
```

- [ ] **Step 4: Update test_validator.py**

Change batch fixture from `"rust"` to `"node"`:
```python
# OLD
for name in ["python", "rust"]:

# NEW
for name in ["python", "node"]:
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 6: Run ruff**

Run: `uv run ruff check src/ tests/ && uv run ruff format src/ tests/`
Expected: All clean

- [ ] **Step 7: Commit**

```bash
git add tests/
git commit -m "test: update tests for 2-language support (python, node)"
```

---

### Task 2: Update CLI and CLAUDE.md

**Files:**
- Modify: `src/devcc/cli.py`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update cli.py batch docstring**

```python
# OLD
"""Create devcontainers for language-agent pair combinations.

\b
Produces 6 languages x (5 agents + no-agent) = 36 templates.
...
  e.g., python/, python-claude-code/, rust-codex/

# NEW
"""Create devcontainers for language-agent pair combinations.

\b
Produces 2 languages x (5 agents + no-agent) = 12 templates.
...
  e.g., python/, python-claude-code/, node-codex/
```

- [ ] **Step 2: Update CLAUDE.md**

```markdown
# OLD
uv run devcc batch                               # generate all 36 templates

# NEW
uv run devcc batch                               # generate all 12 templates
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest -q`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add src/devcc/cli.py CLAUDE.md
git commit -m "docs: update CLI help and CLAUDE.md for 2-language support"
```

---

### Task 3: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README.md**

Remove rust, r, julia, c-cpp-fortran from:
- The `devcc list` output example
- The `devcc create -l rust` example (replace with `devcc create -l node`)
- Any other references to removed languages

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README for 2-language support"
```

---

### Task 4: Update Spec and Plan docs

**Files:**
- Modify: `.dev/spec/260317-spec-devcc-package.md`
- Modify: `.dev/plan/260317-plan-devcc-impl.md`

- [ ] **Step 1: Update spec**

Update the "Supported Languages" table to only list `python` and `node` with `"latest"` versions. Update all batch counts from 36 to 12, and remove references to `rust`, `r`, `julia`, `c-cpp-fortran`. Update the `6 × 6 = 36` formula to `2 × 6 = 12`.

- [ ] **Step 2: Update plan**

Same changes in the implementation plan — language lists, counts, test expectations.

- [ ] **Step 3: Commit**

```bash
git add .dev/
git commit -m "docs: update spec and plan for 2-language support"
```

---

### Task 5: Commit Staged Language Fragment Changes

**Files:**
- Already staged: language fragment deletions and modifications

- [ ] **Step 1: Commit the staged data changes**

```bash
git commit -m "feat: reduce languages to python and node with latest defaults"
```

This commits the already-staged deletions of `rust.json`, `r.json`, `julia.json`, `c-cpp-fortran.json` and the version changes in `python.json` and `node.json`.

---

### Task 6: Final Verification

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 2: Run ruff**

Run: `uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/`
Expected: All clean

- [ ] **Step 3: Test CLI end-to-end**

```bash
uv run devcc list
uv run devcc create -l python -a claude-code -o /tmp/devcc-verify
uv run devcc batch -o /tmp/devcc-verify-batch
uv run devcc validate /tmp/devcc-verify-batch
```

Expected: `list` shows 2 languages, batch generates 12 templates, all valid.

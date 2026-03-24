# Rubric: oxy-etl-builder

Score each item ✅ pass or ❌ fail after running the skill.
Items are split into **must-pass** (skill fails eval if any of these fail) and
**should-pass** (quality improvements to track over time).

---

## MUST-PASS — Runtime Correctness

These items mean the ETL pipeline will fail to run if they don't pass.

- [ ] **M1** Created `etl/sources/<provider>/client.py` with an API client class.
- [ ] **M2** Created `etl/sources/<provider>/<entity>_source.py` with DLT source.
- [ ] **M3** Created `etl/runners/<provider>_<entity>.py` with a runner.
- [ ] **M4** `import dlt` is present in the source file.
- [ ] **M5** At least one function is decorated with `@dlt.resource(...)`.
- [ ] **M6** `@dlt.resource` specifies `write_disposition` (e.g. `merge` or `replace`) and `primary_key`.
- [ ] **M7** No hardcoded API keys or passwords in any file — credentials come from environment variables.
- [ ] **M8** `python -m py_compile etl/sources/<provider>/client.py` exits without error.
- [ ] **M9** `python -m py_compile etl/sources/<provider>/<entity>_source.py` exits without error.
- [ ] **M10** `python -m py_compile etl/runners/<provider>_<entity>.py` exits without error.

---

## SHOULD-PASS — Quality & Best Practice

- [ ] **Q1** Skill activation message appeared in Claude output on the first trigger prompt. If not shown, note whether output quality still matched skill behavior and retest in a fresh session.
- [ ] **Q2** For new projects: core framework created (`etl/core/pipeline.py`, etc.) before source code.
- [ ] **Q3** Runner extends `BasePipelineRunner` (or equivalent base class) rather than being a standalone script.
- [ ] **Q4** For incremental loading: uses `dlt.sources.incremental[...]` or equivalent incremental pattern.
- [ ] **Q5** Client includes rate limiting or retry logic (sleep, retry, or exception handling on HTTP errors).
- [ ] **Q6** File naming follows convention: `client.py`, `<entity>_source.py`, `<provider>_<entity>.py`.
- [ ] **Q7** Runner has CLI support so it can be invoked as `uv run python -m etl.runners.<runner> run`.

---

## Notes

**Commands to verify manually:**
```bash
# Syntax checks
python -m py_compile etl/sources/<provider>/client.py
python -m py_compile etl/sources/<provider>/<entity>_source.py
python -m py_compile etl/runners/<provider>_<entity>.py

# Check DLT usage
grep "import dlt" etl/sources/<provider>/<entity>_source.py
grep "@dlt.resource" etl/sources/<provider>/<entity>_source.py
grep "write_disposition" etl/sources/<provider>/<entity>_source.py

# Check no hardcoded credentials
grep -r "api_key\s*=\s*['\"]" etl/sources/
grep -r "password\s*=\s*['\"]" etl/sources/

# Test run (no actual API calls)
uv run python -m etl.runners.<provider>_<entity> test
```

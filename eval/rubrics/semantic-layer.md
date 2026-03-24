# Rubric: oxy-semantic-layer

Score each item ✅ pass or ❌ fail after running the skill.
Items are split into **must-pass** (skill fails eval if any of these fail) and
**should-pass** (quality improvements to track over time).

---

## MUST-PASS — Runtime Correctness

These items mean oxy will fail or produce wrong results if they don't pass.

- [ ] **M1** Skill read `.databases/` directory to discover schema before generating files. Column and table names in output match what's in `.databases/` — no hallucinated names.
- [ ] **M2** Created at least one `.view.yml` per major table. Files are in `semantics/views/`.
- [ ] **M3** Created at least one `.topic.yml`. File is in `semantics/topics/`.
- [ ] **M4** Entity `key` values reference a `name` from the `dimensions` list — NOT a raw database column name. Verify: the key value appears as a `name:` under `dimensions:` in the same view.
- [ ] **M5** Each view has `name`, `datasource`, and `table` fields. `datasource` matches a database name in `config.yml`.
- [ ] **M6** Topic `base_view` value matches the `name` field of an existing view file exactly.
- [ ] **M7** All dimension `type` values are one of: `string`, `number`, `date`, `datetime`, `boolean`. No other values used.
- [ ] **M8** All measure `type` values are one of: `sum`, `average`, `count`, `count_distinct`, `min`, `max`, `median`, `stddev`, `custom`. No other values used.
- [ ] **M9** `oxy build` exits without error after all files are created. (Run manually if skill skipped it.)

---

## SHOULD-PASS — Quality & Best Practice

These improve usability and natural language support but won't break oxy.

- [ ] **Q1** Skill activation message appeared in Claude output on the first trigger prompt.
- [ ] **Q2** Skill ran `oxy build` automatically after creating files (without needing user to ask).
- [ ] **Q3** At least one dimension per view has `synonyms` defined (aids natural language queries).
- [ ] **Q4** Categorical dimensions (status, type, source, etc.) have `samples` defined.
- [ ] **Q5** View `description` and dimension `description` fields contain meaningful business context (not just the column name repeated).
- [ ] **Q6** Topic `views` array includes all related views, not just one.

---

## Notes

**The #1 failure is M4**: `key: order_id` where `order_id` is the database column name rather
than a dimension name. Always check this first.

**M9 is the ground truth check.** `oxy validate` does NOT validate view/topic files; only
`oxy build` processes them.

**Q1 failure** is informational. If the skill name didn't appear but the output quality was
correct, it likely means the skill activated silently or context was retained. Start a fresh
session to verify.

**Commands to verify manually:**
```bash
oxy build

# Check entity keys reference dimension names
grep -A5 "entities:" semantics/views/*.view.yml
grep "name:" semantics/views/*.view.yml | head -20
```

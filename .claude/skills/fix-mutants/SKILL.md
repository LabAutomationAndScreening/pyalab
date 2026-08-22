---
name: fix-mutants
description: Runs mutmut mutation testing and closes the gaps it finds by strengthening tests until surviving mutants are killed. Use when the user wants to run mutation testing, kill surviving mutants, improve test effectiveness, or says "fix mutants" / "run mutmut".
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, AskUserQuestion
---

# Fix Mutants

## Purpose

A surviving mutant is a change to the source that the test suite failed to
detect — proof of a missing or weak assertion, not a code bug. This skill runs
mutmut, enumerates surviving mutants, and drives a per-mutant loop: understand
the mutation, strengthen the test that should have caught it, and verify the
mutant is now killed.

The deterministic mechanics (running mutmut, parsing its per-file `.meta`
state, computing status, re-verifying a single mutant) live in the Python
scripts beside this file. The model's job is the judgement: deciding which
gap is worth closing and writing the right assertion.

## Prerequisites

- There exists a `pyproject.toml` file with a `[tool.mutmut]` table.
- `uv` is available; mutmut is installed in the project environment.
- Scripts can be run from the repo root or from inside the subfolder containing `pyproject.toml` —
  they locate the `[tool.mutmut]` root by searching upward then up to two
  levels downward.

> **Invoke every script by its path directly** (e.g.
> `{ABSOLUTE_PATH_TO_REPOSITORY_ROOT}/.claude/skills/fix-mutants/list-survived.py`). They are executable,
> stdlib-only, and have shebangs. Do **not** prefix with `uv run python`.
> The scripts call `uv run mutmut` internally.

## Conventions

**Always show file paths to the user as absolute paths, with the line number
appended** (e.g. `/workspaces/my-app/backend/src/foo.py:55`) so they are
Ctrl+clickable in VS Code. Relative paths (`src/foo.py`) are not clickable.
This applies to every file path in a user-facing message: the mutated source
file, the test files in `tests_for_line`, and any test file you edit.

The scripts emit `source_file` values relative to the subfolder containing
`pyproject.toml`, and every script also emits that subfolder as an absolute
`backend_root` field. Construct displayed paths as
`<backend_root>/<source_file>:<line>`. Exception: the briefing block rendered
by `group-by-line.py` already contains absolute paths — paste it as-is; this
construction rule is for paths you compose yourself (e.g. a test file you
edited).

## Workflow

### Step 0: Decide how to start

```bash
.claude/skills/fix-mutants/check-results.py
```

This runs `mutmut results` and reports whether a prior run exists.

**REQUIRED — always ask via `AskUserQuestion` before proceeding:**

- If `has_results` is **false** (no prior run): offer one option only:
  - **Run mutmut (clean)** — wipe `mutants/` and run from scratch

- If `has_results` is **true** (prior run exists): offer three options:
  - **Run mutmut (clean)** — wipe `mutants/` and run from scratch; most
    trustworthy baseline but takes the longest
  - **Run mutmut (cached)** — reuse existing mutants, only re-test what changed;
    faster, good for iterating after test edits
  - **Use existing results** — skip straight to Step 2 using the results already
    on disk; fastest, use when mutmut was just run externally

Then proceed to Step 1 (if running mutmut) or Step 2 (if using existing results).

### Step 1: Run the mutation suite

```bash
# clean:
.claude/skills/fix-mutants/run-mutmut.py --clean

# cached:
.claude/skills/fix-mutants/run-mutmut.py
```

Output is a JSON status breakdown:

```json
{ "generated": "done in 2230ms (23 files mutated, 65 ignored, 0 unmodified)",
  "counts": {"killed": 180, "survived": 22, "no tests": 3},
  "total": 205, "actionable": 25 }
```

This step can take minutes (full suite per mutant). If `actionable` is 0,
report a clean bill of health and stop.

### Step 2: Enumerate the gaps

```bash
.claude/skills/fix-mutants/list-survived.py
```

Returns actionable mutants (`survived` + `no tests`) grouped by source file.
Present a summary to the user — count per file — and confirm scope.

**REQUIRED — do not skip even if there is only one file or all counts are small:**
Use `AskUserQuestion` to ask which file(s) to work through (or "all"). Only
proceed to Step 3 after the user answers.

> **Triage note.** `no tests` means the mutated line is executed by *no* test
> at all — the gap is a missing test, not a weak assertion. `survived` means a
> test runs the line but does not assert on its effect. Both are in scope;
> mention which kind each mutant is when presenting it.

### Step 3: Per-line-group loop

The **unit of work is a line group**: all surviving mutants that share the same
`source_file` and `line`. A single strengthened assertion usually kills every
mutant on that line at once, so treat them together.

The loop is driven by calling `group-by-line.py` repeatedly. Each call returns
the **next unresolved group** based on live meta state — calling it again
without resolving the current group just returns the same group. Accumulate
`--skip-line N` flags for any lines the user has chosen to skip.

```bash
# First call (and after each kill):
.claude/skills/fix-mutants/group-by-line.py <source_file> [--skip-line N ...]
```

When a group remains, the script's stdout has two parts:

1. A **pre-rendered briefing block** between the marker lines
   `=== MUTANT BRIEFING — PASTE TO USER VERBATIM ===` and
   `=== END MUTANT BRIEFING ===`. The script has already done all the
   formatting work: absolute Ctrl+clickable `path:line` header, remaining-line
   count, original source, every mutant's fenced diff, and exercising tests as
   absolute paths. You never compose this block yourself.
2. A `---MACHINE-READABLE---` delimiter followed by the JSON payload (use this
   for `line`, mutant `key`s, and `tests_for_line`).

When `done: true` is returned (JSON only, no briefing), all groups for this
file are resolved.

> **STRICT ORDER per group — do not deviate:**
> 1. Run `group-by-line.py`.
> 2. **Paste the briefing block** into a normal text message.
> 3. Read the source and tests; form a view.
> 4. Emit `My plan: ...` as a normal text message.
> 5. AskUserQuestion (short question only).
>
> **Never place any tool call between steps 1 and 2 — pasting the briefing is
> the single next action after the script returns. Never call AskUserQuestion
> before the briefing block appears in one of your text messages. Never
> recompose, summarize, reformat, or trim the block — the script rendered it;
> your only job is to relay it. The user cannot expand tool results: if you do
> not paste the block, the user is deciding blind.**

The five steps in detail:

1. **Paste the briefing.** Copy everything between the two marker lines
   (markers themselves excluded) into your next text message, byte-for-byte.
   Do not wrap it in an outer code fence — it already contains its own fenced
   blocks. This applies even when the situation seems obvious, the group is
   small, or brevity/compression guidance (e.g. caveman mode) is active — the
   block is skill-mandated payload, not prose to compress.

2. **Read and analyze.** Only after the briefing is pasted: read the
   `source_file` around `line` and the tests in `tests_for_line`. Form a
   view: *what observable behavior changes under these mutations, and why
   does no current assertion notice?*

3. **Present the plan.** Emit as a normal text message:

   ```
   My plan: <which test to add/strengthen and the assertion that distinguishes
   original from all mutants on this line>
   ```

4. **Ask.** Use AskUserQuestion with exactly this shape:
   - Question: `Strengthen the test for this line?` — only this short
     question; never the diffs, facts, or plan.
   - Options: **Strengthen test** / **Skip (equivalent or not worth it)** /
     **Discuss first**.

   Self-check before making this call: does one of your text messages for
   *this* group contain a fenced diff and an absolute `path:line`? If not,
   you skipped step 1 — paste the briefing now, then ask.

   - Some mutants are *equivalent* — the mutated code is behaviorally identical
     to the original (e.g. a mutation inside dead code, or a default that is
     always overridden). These cannot be killed and should be skipped, not
     chased. Call them out explicitly; offer the user a pragma block or a
     `do_not_mutate` entry as the durable suppression. Single-line
     `# pragma: no mutate` trailing comments are unreliable — use the
     start/end block form, with a comment explaining the rationale as the
     first line inside the block:

     ```python
     # pragma: no mutate start
     # rationale for why these lines cannot be meaningfully mutation-tested
     line_to_exclude()
     # pragma: no mutate end
     ```

5. **Strengthen the test** following the project's TDD discipline. The mutants
   *are* the failing cases: write/adjust the assertion so the test passes on the
   original and would fail on every mutant in the group. Follow `AGENTS.md`
   testing rules (tight mock assertions, no magic values, presence-before-absence,
   etc.). Run the single affected test first (`uv run pytest <path>::<test>
   --no-cov`) and confirm it is green on real code.

6. **Verify every mutant in the group is dead:**
   ```bash
   .claude/skills/fix-mutants/verify-mutant.py <mutant_name>
   ```
   Run for each mutant in the group. Exit 0 = killed. If any survive, the
   assertion doesn't distinguish all variants — return to step 5. Do not call
   `group-by-line.py` again until all are killed (or the user agrees to skip).

7. **Advance:** call `group-by-line.py` again (killed mutants are gone from meta;
   add `--skip-line <line>` if the user chose to skip this group). Process the
   next group returned, or stop if `done: true`.

### Step 4: Re-baseline and report

After a batch, optionally re-run `run-mutmut.py` (no `--clean` is fine) to
confirm the actionable count dropped and no new mutants appeared from edited
tests. Report:

- Mutants killed (with the test added/changed for each)
- Mutants skipped as equivalent (with the suppression applied, if any)
- Remaining actionable count

## Guidelines

**DO**
- Treat each surviving mutant as a precise, executable description of a missing
  assertion.
- Paste the script-rendered briefing block verbatim the moment
  `group-by-line.py` returns — before any analysis or file reading, and well
  before the AskUserQuestion. The question options alone are not enough
  context to decide.
- Verify every fix with `verify-mutant.py` before claiming the gap is closed.
- Identify equivalent mutants honestly rather than contorting a test to kill an
  un-killable mutation.
- Make one logical test change per mutant so a failed verify points at one edit.

**DON'T**
- Modify source code to kill a mutant — the fix is almost always in the tests.
  (If the mutant reveals a real bug, surface it to the user separately; that is
  out of scope for a test-strengthening pass.)
- Weaken or delete other tests to make the suite pass.
- Suppress a mutant (`pragma`/`do_not_mutate`) without the user agreeing it is
  equivalent or out of scope.
- Batch many test edits then one verify — verify per mutant.
- Re-render, summarize, or restyle the briefing block — relay it exactly as
  the script printed it.

## Checklist

- [ ] `check-results.py` → ask user: clean / cached / use existing
- [ ] `run-mutmut.py [--clean]` → baseline status breakdown (skip if using existing)
- [ ] `list-survived.py` → actionable mutants by file; confirm scope with user (AskUserQuestion, required)
- [ ] Per file: `group-by-line.py <source_file>` → paste script-rendered briefing block verbatim as a text message (no tool calls in between) → read source + tests → present plan → approve (AskUserQuestion, required)
- [ ] Strengthen the test; confirm it passes on real code
- [ ] `verify-mutant.py <name>` for every mutant in group → all killed (exit 0) before advancing
- [ ] Re-baseline; report killed / skipped-equivalent / remaining

<!--
============== WARNING ==============================================================================
File is managed by copier template: gh:LabAutomationAndScreening/copier-base-template.git
See .config/.copier-managed-files.json for details.

You are welcome to make changes to this file in your repo if they are custom to your project,
but if the change should be shared with other projects, please backport it to the template repo.
=====================================================================================================
-->

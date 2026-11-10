---
name: gh-create-issue
description: Create a standalone GitHub issue in the current repository (resolved from git remote origin) using gh. User-triggered only. Produces a self-sufficient technical issue body (context, root cause, affected files, acceptance criteria) so another agent can work on it in a fresh session without extra context.
---

# Create standalone GitHub issue

Create an issue in the **current repository** that a *fresh agent session* can work on with zero additional context. The issue body is the only handoff artifact — anything the working agent needs must be in it.

## Process

0. **Resolve the repo.** Run `gh repo view --json nameWithOwner -q .nameWithOwner` (falls back to `git remote get-url origin`) and use the result as `--repo` / API path in every gh command below. Never hardcode a repo name.
1. **Investigate first.** Before writing, reproduce or trace the problem in the codebase:
   - Read the relevant files, run the failing command/test, capture the exact error.
   - Identify the root cause at file/function level, not just the symptom.
   - If this is a feature, note the current behavior and the integration points.
2. **Draft the body** using the template below. Fill every section that applies; write "N/A" with a one-line reason for sections that do not. Never leave a section silently empty.
3. **Show the draft to the user** (title + body) and wait for confirmation. Do not create the issue unconfirmed.
4. **Create it:**

   ```bash
   gh issue create --repo <resolved-owner/repo> --title "<title>" --body-file /tmp/issue-body.md
   ```

   Write the body to a temp file (avoid shell-escaping problems), pass via `--body-file`, delete the temp file after.
5. **Reply with the issue URL.**

## Title format

`<type>: <specific problem or change>` — e.g. `fix: token expiry off-by-one in auth middleware`, `feat: add pagination to /api/items`.

## Body template

````markdown
## Context

What this issue is about in 1-2 sentences. What the system does today.

## Problem / Requirement

Exact problem (with verbatim error string, including stack trace tail if relevant)
or exact requirement for a feature. No fluff, no "it would be nice to".

## Root cause / Analysis

Where the problem lives: file paths, function names, line numbers where stable.
Explain *why* it happens, not just *what* happens. For features: where the new
code plugs in, what existing code to touch, what NOT to touch.

## Reproduction

Exact commands, inputs, and observed vs expected output. Must be runnable
by someone with a clean clone of the repo.

## Constraints

Non-goals, things that must not change (APIs, schema, dependencies, style rules
from AGENTS.md that are especially relevant here).

## Acceptance criteria

Checklist the working agent can verify mechanically:

- [ ] <behavior statement, testable>
- [ ] `make test` passes
- [ ] `make check-all` passes
- [ ] Tests added covering <specific case>

## Done means

Working agent commits with `git commit --trailer Generated-by:<model> -m "<type>: ..."`
and opens a PR referencing this issue (`fixes #<n>` or `closes #<n>` in PR body).
````

## Writing rules

- Technical and dense. No pleasantries, no hedging, no "please note".
- Every claim backed by file path / line / command output. No "somewhere in the app".
- Include exact error strings and failing commands verbatim.
- If reproduction is non-deterministic, state the flake rate and the fastest
  deterministic trigger found.
- If unsure about root cause, say so explicitly in "Root cause / Analysis"
  and list the candidate causes with evidence for each. Never hide uncertainty —
  the working agent must know what is verified vs hypothesized.
- Do not duplicate what AGENTS.md already mandates (commit format, core rules).
  Reference it once in "Done means" / "Constraints".

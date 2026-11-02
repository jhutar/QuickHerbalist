---
name: gh-review-pr
description: Review a PR in jhutar/nasdracak against the Core Rules in AGENTS.md and post structured review comments (diff-level where possible) so another agent can fix them. User-triggered only.
---

# Review PR against Core Rules

Review a PR in `jhutar/nasdracak`. Output is machine-actionable review feedback:
one comment per issue, precise location, concrete fix direction. The audience is
*another agent* — be exact, no prose it has to guess on.

## Input

User provides a PR number or URL. Extract the number.

## Steps

1. **Fetch context:**

   ```bash
   gh pr view <n> --repo jhutar/nasdracak --json title,body,headRefName,baseRefName,additions,deletions,files
   gh pr diff <n> --repo jhutar/nasdracak
   # Read the linked issue if referenced in the PR body, for intent check
   gh pr checks <n> --repo jhutar/nasdracak
   ```

2. **Read full changed files** in the repo (checkout the head ref if local repo
   is on a different branch) — do not review only the diff hunks. Context matters:
   a line that looks fine in the diff may violate Single Responsibility when you
   see the whole function.

3. **Review checklist** — check every item from the "Core Rules" section of
   AGENTS.md, plus the PR-specific items:

   Core Rules:
   - [ ] **Single Responsibility** — new/changed functions small and focused; flag functions that grew beyond ~30 lines doing multiple things.
   - [ ] **Readability** — names descriptive, no cryptic abbreviations.
   - [ ] **No Over-Engineering** — nothing speculative, no premature abstraction, no unused options/params/dead code.
   - [ ] **Error Handling** — fails fast, specific exceptions caught, meaningful log messages; flag bare `except:`, swallowed errors, generic messages.
   - [ ] **No Guessing** — flag fallback defaults, silent input repair, `or "default"` on missing data, any handling that guesses bad input instead of failing.
   - [ ] **Consistency** — style/format/patterns match surrounding codebase.
   - [ ] **Documentation** — every new/changed class, method, function has a docstring.

   PR-specific:
   - [ ] Diff matches the stated intent (linked issue / PR body) — no scope creep.
   - [ ] Tests: new behavior covered, tests match the changed behavior, no deleted/weakened tests without reason.
   - [ ] CI (`gh pr checks`) passing or explainably failing.
   - [ ] No collateral changes: unrelated reformatting, drive-by fixes, lockfile churn.
   - [ ] Commit messages follow repo convention; generated-by trailer present.

4. **Post the review** (ask the user to confirm the comment list first, unless
   they said to post without confirmation):

   - **Diff-level** for issues tied to specific lines — these are the most
     actionable for a fixing agent:
     ```bash
     gh api repos/jhutar/nasdracak/pulls/<n>/comments -f body="<comment>" \
       -f path="<file>" -F line=<line> -F side=RIGHT
     ```
     (Use the file/line in the *new* version. For deleted lines use `side=LEFT`
     and the old line number. For a new hunk without a single line, use
     `commit_id` + `start_side` form if needed.)
   - **General review body** with the overall verdict and any repo-level
     (non-line-specific) findings:
     ```bash
     gh pr review <n> --repo jhutar/nasdracak --comment --body-file /tmp/review.md
     ```

## Comment format

One issue per comment. Format:

```
[<rule name>] <problem in one sentence>.
Fix: <concrete change — code snippet if short, exact description if not>.
```

Rules for the fixing agent to act without follow-up:
- Name the exact Core Rule violated (e.g. `[No Guessing]`, `[Single Responsibility]`).
- State the fix concretely — a snippet or an unambiguous description, not
  "consider refactoring this".
- For Non-blocking nits, prefix with `[nit]` so the fixing agent can prioritize.
- If everything passes, post a single review: `Looks good — Core Rules check
  clean. <one line on what was verified: files count, tests, CI state>.`
- Do not post comments for things the PR cannot fix (repo-wide debt) — list
  those in your summary to the user instead.

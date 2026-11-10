---
name: gh-load-issue
description: Load full context of a GitHub issue (body, comments, in-code review comments) in the current repository (gh auto-detects from git remote) and summarize it so work can start immediately in a fresh session. User-triggered only.
---

# Load GitHub issue context

Load an issue from the **current repository** in full — body, timeline comments, and
in-code review comments from linked PRs — then produce a working brief and start.

## Input

User provides an issue number (e.g. `42`) or issue URL. Extract the number.

Run all commands from inside a checkout of the target repository — `gh` auto-detects the repo from the git remote. For `gh api` use the `repos/{owner}/{repo}/...` placeholder form (bare relative paths are NOT expanded). Add explicit `--repo owner/repo` only when running outside a checkout. Never hardcode a repo name.

## Fetch steps

Run all of these; do not skip the review comments step:

```bash
# 1. Issue body + metadata (labels, state, assignees)
gh issue view <n> --json title,body,labels,state,author

# 2. All timeline comments (issue comments, cross-references, etc.)
gh api repos/{owner}/{repo}/issues/<n>/comments --jq '.[] | "--- \(.user.login) (\(.created_at))\n\(.body)"'

# 3. Linked PRs and their review feedback
gh pr list --state all --search "linked:issue:<n>" --json number,title,state,reviewDecision
# For each linked PR:
gh pr view <pr> --json title,body,state,reviewDecision
gh pr comments <pr> --json author,body,path,line,createdAt
# In-code review comments (diff-level):
gh api repos/{owner}/{repo}/pulls/<pr>/comments --jq '.[] | "--- \(.user.login) @ \(.path):\(.line)\n\(.body)"'
```

Also check PR review summary comments (not just diff-level):
`gh api repos/{owner}/{repo}/pulls/<pr>/reviews --jq '.[] | "--- \(.user.login) [\(.state)]\n\(.body)"'`

## Output: working brief

After fetching, produce this before touching code:

1. **Goal** — one line: what done means, per the issue acceptance criteria.
2. **Current state** — is it untouched, or is a linked PR already in progress?
   If a PR exists: its branch, what it already does, what reviews flagged as unfixed.
3. **Open items** — bullet list: acceptance criteria not yet met, unresolved
   review comments (quote each, mark which files/lines), unresolved discussion comments.
4. **Entry points** — files to read first, commands to run to reproduce current state
   (`git fetch && git checkout <branch>` if continuing a PR, or list of files to read for a fresh start).
5. **Unresolved questions** — anything ambiguous in the issue thread that should
   be clarified in the issue (post the question as a comment via
   `gh issue comment <n> --body "..."` only if the user
   confirms; otherwise just list it).

## Then

Follow the repo AGENTS.md workflow: plan, implement, test, commit, PR referencing
the issue. If a linked PR already exists, continue on that branch rather than
opening a new one, unless the user says otherwise.

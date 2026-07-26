#!/usr/bin/env bash
set -euo pipefail

SPEC_DIR=${1:-""}
AGENT_CMD=${2:-"../agent-in-container/run-pi.sh"}

# Configurable options via environment variables
YOLO_MODEL="${YOLO_MODEL:-google/gemma-4-26B-A4B-it-qat-q4_0-gguf}"
MAX_RETRIES="${MAX_RETRIES:-3}"

if [[ -z "$SPEC_DIR" || ! -d "$SPEC_DIR" ]]; then
    echo "Usage: $0 <path-to-spec-dir> [path-to-agent-cmd]"
    echo "Example: $0 specs/002-sprite-manager"
    exit 1
fi

TASKS_FILE="$SPEC_DIR/tasks.md"
if [[ ! -f "$TASKS_FILE" ]]; then
    echo "Error: $TASKS_FILE not found."
    exit 1
fi

# Pre-flight Check: Ensure the git working directory is completely clean before starting.
if [[ -n $(git status --porcelain) ]]; then
    echo "FATAL: Git working directory is not clean. Please commit or stash existing changes before running the YOLO loop."
    git status --porcelain
    exit 1
fi

# Extract all tasks (e.g., T001, T002) that are not checked off yet
PENDING_TASKS=$(grep -oE '\[ \] T[0-9]{3}' "$TASKS_FILE" | awk '{print $2}')

if [[ -z "$PENDING_TASKS" ]]; then
    echo "No pending tasks found in $TASKS_FILE."
    exit 0
fi

# Convert string to array
mapfile -t TASKS_ARRAY <<< "$PENDING_TASKS"

for i in "${!TASKS_ARRAY[@]}"; do
    CURR_ID="${TASKS_ARRAY[$i]}"
    PREV_ID="None"
    NEXT_ID="None"

    if [[ $i -gt 0 ]]; then
        PREV_ID="${TASKS_ARRAY[$i-1]}"
    fi
    if [[ $i -lt $((${#TASKS_ARRAY[@]} - 1)) ]]; then
        NEXT_ID="${TASKS_ARRAY[$i+1]}"
    fi

    echo "##### $(date --utc -Ins) Started $CURR_ID #####"

    PROMPT="
You are an expert software engineer running in YOLO mode. Your mission is to implement task **$CURR_ID** defined in \`$TASKS_FILE\`.

### 1. Context Assembly
- Read the project spec: \`$SPEC_DIR/spec.md\`
- Read the implementation plan: \`$SPEC_DIR/plan.md\`
- Read contracts or data models in \`$SPEC_DIR\` if they exist.
- Read the task list: \`$TASKS_FILE\`. Focus strictly on:
  - **Previous Task ($PREV_ID)**: Understand what was just built (if applicable).
  - **Current Task ($CURR_ID)**: This is your primary objective.
  - **Next Task ($NEXT_ID)**: Ensure your interfaces are compatible and don't leave broken stubs for the next agent.

### 2. Codebase Investigation
- Search the codebase to locate target files.
- Identify and reuse existing helper functions. DO NOT duplicate code or hardcode paths.

### 3. Implementation and Self-Correction Loop
- Perform targeted, surgical changes strictly for **$CURR_ID**.
- Run the test suite: \`make test\`.
- If tests fail, diagnose and self-correct.
- Run linters/formatters: \`make check-all\` (or equivalent). Fix all issues.

### 4. State Tracking & Git Commit
- Once tests and linters pass, edit \`$TASKS_FILE\` to change the checkbox for $CURR_ID from \`[ ]\` to \`[x]\`.
- Run \`git diff\` to self-review. Ensure no debug code is left.
- Stage ONLY the files modified for this task and commit with:
  \`git commit --trailer \"Generated-by:$YOLO_MODEL\" -m \"feat: Spec $(basename "$SPEC_DIR") task $CURR_ID\"\`
"

    # 1. Initial Agent Invocation
    $AGENT_CMD --print "$PROMPT"

    # 2. Outer Validation Loop (Make sure the agent actually succeeded and left a clean state)
    SUCCESS=false
    for attempt in $(seq 1 "$MAX_RETRIES"); do
        ERRORS=""

        echo "##### $(date --utc -Ins) Validating state for $CURR_ID (Attempt $attempt) #####"

        # Check A: Was the task marked as complete?
        if grep -q "\[ \] $CURR_ID" "$TASKS_FILE"; then
            ERRORS+="* Task $CURR_ID was not marked as completed ([x]) in $TASKS_FILE.\n"
        fi

        # Check B: Do the linters pass?
        if ! make check-all > /tmp/yolo_lint_out.txt 2>&1; then
            ERRORS+="* Code quality checks (make check-all) failed:\n$(cat /tmp/yolo_lint_out.txt)\n\n"
        fi

        # Check C: Do the tests pass?
        if ! make test > /tmp/yolo_test_out.txt 2>&1; then
            ERRORS+="* Tests (make test) failed:\n$(cat /tmp/yolo_test_out.txt)\n\n"
        fi

        # Check D: Is the Git working directory clean?
        if [[ -n $(git status --porcelain) ]]; then
            ERRORS+="* Git working directory is not clean. You must stage and commit ALL files changed or created:\n$(git status --porcelain)\n\n"
        fi

        # If no errors accumulated, we are good to proceed to the next task.
        if [[ -z "$ERRORS" ]]; then
            SUCCESS=true
            break
        fi

        # 3. Agent Re-invocation (Self-Correction via --continue)
        echo -e "##### $(date --utc -Ins) Validation failed. Errors found:\n$ERRORS"
        echo "##### Re-running agent with --continue to fix the issues. #####"

        FEEDBACK="Your previous execution left the repository in an incomplete or broken state. Please fix the following errors:\n\n$ERRORS\n\nEnsure you write correct code, fix all tests and linters, mark the task as complete in $TASKS_FILE, and cleanly commit ALL changes with trailer 'Generated-by:$YOLO_MODEL'."

        $AGENT_CMD --continue --print "$FEEDBACK"
    done

    # Circuit Breaker: If we exhausted retries and it still fails
    if [[ "$SUCCESS" != "true" ]]; then
        echo "##### $(date --utc -Ins) FATAL: $CURR_ID could not be completed successfully after $MAX_RETRIES validation attempts. Halting pipeline. #####"
        exit 1
    fi

    echo "##### $(date --utc -Ins) Finished and Validated $CURR_ID #####"
done

echo "All pending tasks completed successfully!"

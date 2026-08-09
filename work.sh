#!/bin/bash

set -euo pipefail

model=unsloth/Qwen3.6-35B-A3B-GGUF/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf
###model=unsloth/gemma-4-26B-A4B-it-GGUF/gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf

###for code_file in $( find src/ -name \*.py | grep -v -e '__init__\.py' -e '__main__\.py' ); do
###    echo "=== $( date --utc -Ins ) Documenting $code_file ==="
###    ../agent-in-container/run-pi.sh --thinking xhigh -p @AGENTS.md "@${code_file}" "For every class/method/function defined in ${code_file} make sure there is at least 1 line long docstring. When committing follow 'Workflow Instructions' (current model is '${model}')."
###done
###exit

for code_file in $( find src/ -name \*.py | grep -v -e '__init__\.py' -e '__main__\.py' -e "profiles.py" ); do
    echo "=== $( date --utc -Ins ) Reviewing $code_file ==="
    ../agent-in-container/run-pi.sh --thinking xhigh -p @AGENTS.md "@${code_file}" "Suggest 0 - 3 most important flaws in ${code_file} to allign with our Coding Rules. For each identified issue write standalone bug report './specs/task-<id>.md' so the report can be handed over to standalone agent."
    echo "=== $( date --utc -Ins ) Issues ==="
    git status
    ls -al ./specs/task-*.md

    for task_file in specs/task-*.md; do
        echo "=== $( date --utc -Ins ) Fixing $task_file ==="
        ../agent-in-container/run-pi.sh --thinking high -p @AGENTS.md "@${task_file}" "Fix ${task_file} in ${code_file} using AGENTS.md 'Core Rules' and 'Workflow Instructions'. ALWAYS check with \`make test\` and \`make check-all\` and resolve reported issues. Do not commit $task_file itself. Once clean, commit with \`git commit --trailer 'Generated-by:${model}' -m '...'."
        if make test &>/dev/null && make check-all &>/dev/null && [ -z "$(git status --untracked-files=no --porcelain)" ]; then
            echo "=== $( date --utc -Ins ) Clean ==="
            rm "${task_file}"
        else
            echo "=== $( date --utc -Ins ) Dirty ==="
            git status --untracked-files=no
            git diff
            git reset --hard
        fi
    done
done

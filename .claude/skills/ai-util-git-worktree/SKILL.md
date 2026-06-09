---
name: ai-util-git-worktree
description: "Manage git worktrees for parallel feature work. Use this skill when the user says 'worktree', 'new worktree', 'list worktrees', 'remove worktree', 'clean worktrees', or wants to work on a feature in an isolated worktree. Supports: /ai-util-git-worktree new <branch-name>, /ai-util-git-worktree list, /ai-util-git-worktree remove <name>, /ai-util-git-worktree clean."
user_invocable: true
effort: medium
---

# /ai-util-git-worktree — Git Worktree Manager

Manage git worktrees for parallel feature work using a Python script bundled with this skill.

## Script Location

The worktree script lives at `~/.claude/skills/ai-util-git-worktree/worktree.py` (global install). All commands below invoke it via `python3`.

```bash
WORKTREE_SCRIPT="$HOME/.claude/skills/ai-util-git-worktree/worktree.py"
```

This skill works in any git repository. The script auto-detects the repo root via `git rev-parse` and places worktrees in `.worktrees/` at the repo root.

## Commands

Parse the user's arguments and run the appropriate command:

### `/ai-util-git-worktree new <branch-name> [--base <branch>]`

```bash
python3 "$WORKTREE_SCRIPT" new <branch-name> --base <branch>
```

- `branch-name`: Used exactly as-is for both the git branch and the `.worktrees/` directory name.
- `--base`: Base branch to create from. Defaults to `develop`.

After creation, use `AskUserQuestion` to ask if they want to switch to the new worktree. Options:

1. **"Switch to it"** — `cd` to the worktree path in Bash and continue working from there. Use absolute paths for all subsequent `Read`/`Edit`/`Write` tool calls since the session's primary working directory does not change.
2. **"Stay here"** — Print the path and suggest `cd <path> && claude` for manual switching later.

### `/ai-util-git-worktree list`

```bash
python3 "$WORKTREE_SCRIPT" list
```

Shows all worktrees in `.worktrees/` with branch name and dirty status.

### `/ai-util-git-worktree remove <name> [--force] [--keep-branch] [--delete-branch]`

```bash
python3 "$WORKTREE_SCRIPT" remove <name> [--force] [--keep-branch] [--delete-branch]
```

Removes the worktree. Prompts about uncommitted changes unless `--force`. Asks about branch deletion unless `--keep-branch` or `--delete-branch` is specified.

**Important:** If the script prompts for interactive input (uncommitted changes confirmation or branch deletion), use `--force` and `--delete-branch` (or `--keep-branch`) flags instead — Claude Code cannot respond to interactive prompts. Ask the user what they want before running the command.

### `/ai-util-git-worktree clean`

```bash
python3 "$WORKTREE_SCRIPT" clean
```

Prunes stale git worktree references and reports orphaned directories.

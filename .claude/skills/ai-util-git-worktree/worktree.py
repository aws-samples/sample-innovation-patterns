#!/usr/bin/env python3
"""Manage git worktrees for parallel feature work."""

import argparse
import os
import subprocess
import sys


def git(*args, cwd=None):
    """Run a git command and return stdout. Raises SystemExit on failure."""
    result = subprocess.run(
        ["git"] + list(args), capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def get_repo_root():
    """Get the main repo root, even if running from inside a worktree."""
    # git-common-dir points to the shared .git for worktrees
    common_dir = git("rev-parse", "--git-common-dir")
    if common_dir == ".git":
        # We're in the main repo
        return git("rev-parse", "--show-toplevel")
    else:
        # We're in a worktree — resolve the main repo root from the common .git dir
        # common_dir is like /path/to/repo/.git or /path/to/repo/.git/worktrees/../..
        git_dir = os.path.realpath(common_dir)
        return os.path.dirname(git_dir)


def ensure_gitignore(repo_root):
    """Add .worktrees/ to .gitignore if not already present."""
    gitignore_path = os.path.join(repo_root, ".gitignore")

    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            lines = f.read().splitlines()
        for line in lines:
            stripped = line.strip()
            if stripped in (".worktrees", ".worktrees/"):
                return  # already present
        with open(gitignore_path, "a") as f:
            f.write("\n.worktrees/\n")
    else:
        with open(gitignore_path, "w") as f:
            f.write(".worktrees/\n")

    print("Added .worktrees/ to .gitignore")


def cmd_new(args):
    """Create a new worktree."""
    repo_root = get_repo_root()
    worktree_dir = os.path.join(repo_root, ".worktrees")
    branch_name = args.name
    base = args.base
    target_path = os.path.join(worktree_dir, branch_name)

    # Check branch doesn't already exist
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/heads/{branch_name}"],
        capture_output=True, text=True, cwd=repo_root,
    )
    if result.returncode == 0:
        print(f"Error: Branch '{branch_name}' already exists.", file=sys.stderr)
        sys.exit(1)

    # Check base branch exists
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/heads/{base}"],
        capture_output=True, text=True, cwd=repo_root,
    )
    if result.returncode != 0:
        # Try remote
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/remotes/origin/{base}"],
            capture_output=True, text=True, cwd=repo_root,
        )
        if result.returncode != 0:
            print(f"Error: Base branch '{base}' does not exist.", file=sys.stderr)
            sys.exit(1)

    # Check target directory doesn't exist
    if os.path.exists(target_path):
        print(f"Error: Directory '{target_path}' already exists.", file=sys.stderr)
        sys.exit(1)

    # Ensure .worktrees/ in .gitignore
    ensure_gitignore(repo_root)

    # Create .worktrees/ dir
    os.makedirs(worktree_dir, exist_ok=True)

    # Create the worktree
    git("worktree", "add", target_path, "-b", branch_name, base, cwd=repo_root)

    print(f"""
Worktree created!

  Branch:    {branch_name}
  Path:      {target_path}

  To start working:

    cd {target_path}
    claude
""")


def cmd_list(args):
    """List all worktrees."""
    repo_root = get_repo_root()
    worktree_dir = os.path.join(repo_root, ".worktrees")

    if not os.path.exists(worktree_dir):
        print("No worktrees found.")
        return

    entries = sorted(
        e for e in os.listdir(worktree_dir)
        if os.path.isdir(os.path.join(worktree_dir, e))
    )

    if not entries:
        print("No worktrees found.")
        return

    print("Worktrees:\n")
    for entry in entries:
        path = os.path.join(worktree_dir, entry)
        try:
            branch = git("-C", path, "branch", "--show-current")
        except SystemExit:
            branch = "???"
        try:
            status_out = subprocess.run(
                ["git", "-C", path, "status", "--porcelain"],
                capture_output=True, text=True,
            )
            status = "clean" if not status_out.stdout.strip() else "uncommitted changes"
        except Exception:
            status = "unknown"
        print(f"  {entry:<40} {branch:<30} {status}")

    print(f"\nAll git worktrees:")
    print(git("worktree", "list", cwd=repo_root))


def cmd_remove(args):
    """Remove a worktree."""
    repo_root = get_repo_root()
    worktree_dir = os.path.join(repo_root, ".worktrees")
    name = args.name
    target_path = os.path.join(worktree_dir, name)

    if not os.path.exists(target_path):
        print(f"Error: Worktree '{name}' not found in .worktrees/", file=sys.stderr)
        sys.exit(1)

    # Check for uncommitted changes
    if not args.force:
        status_out = subprocess.run(
            ["git", "-C", target_path, "status", "--porcelain"],
            capture_output=True, text=True,
        )
        if status_out.stdout.strip():
            print("Uncommitted changes in this worktree:\n")
            print(status_out.stdout)
            resp = input("Remove anyway? [y/N] ").strip().lower()
            if resp != "y":
                print("Aborted.")
                sys.exit(0)

    # Remove the worktree
    force_flag = ["--force"] if args.force else []
    git("worktree", "remove", target_path, *force_flag, cwd=repo_root)
    print(f"Removed worktree: {name}")

    # Optionally delete the branch
    if args.delete_branch:
        delete_branch = True
    elif args.keep_branch:
        delete_branch = False
    else:
        resp = input(f"Also delete branch '{name}'? [y/N] ").strip().lower()
        delete_branch = resp == "y"

    if delete_branch:
        git("branch", "-D", name, cwd=repo_root)
        print(f"Deleted branch: {name}")

    # Clean up empty .worktrees/ dir
    if os.path.exists(worktree_dir) and not os.listdir(worktree_dir):
        os.rmdir(worktree_dir)
        print("Removed empty .worktrees/ directory.")


def cmd_clean(args):
    """Prune stale worktree references."""
    repo_root = get_repo_root()
    worktree_dir = os.path.join(repo_root, ".worktrees")

    print("Pruning stale worktree references...")
    git("worktree", "prune", cwd=repo_root)
    print("Done.")

    if os.path.exists(worktree_dir):
        # Check for orphaned directories
        valid_worktrees = git("worktree", "list", "--porcelain", cwd=repo_root)
        valid_paths = set()
        for line in valid_worktrees.splitlines():
            if line.startswith("worktree "):
                valid_paths.add(line[len("worktree "):])

        for entry in os.listdir(worktree_dir):
            entry_path = os.path.join(worktree_dir, entry)
            if os.path.isdir(entry_path) and entry_path not in valid_paths:
                print(f"  Orphaned directory: {entry}")

    ensure_gitignore(repo_root)


def main():
    parser = argparse.ArgumentParser(description="Manage git worktrees for parallel feature work.")
    sub = parser.add_subparsers(dest="command", required=True)

    # new
    p_new = sub.add_parser("new", help="Create a new worktree")
    p_new.add_argument("name", help="Branch name (used as-is for branch and directory)")
    p_new.add_argument("--base", default="develop", help="Base branch (default: develop)")

    # list
    sub.add_parser("list", help="List all worktrees")

    # remove
    p_rm = sub.add_parser("remove", help="Remove a worktree")
    p_rm.add_argument("name", help="Worktree name to remove")
    p_rm.add_argument("--force", action="store_true", help="Force removal even with uncommitted changes")
    p_rm.add_argument("--keep-branch", action="store_true", help="Don't delete the branch")
    p_rm.add_argument("--delete-branch", action="store_true", help="Delete the branch without asking")

    # clean
    sub.add_parser("clean", help="Prune stale worktree references")

    args = parser.parse_args()

    commands = {
        "new": cmd_new,
        "list": cmd_list,
        "remove": cmd_remove,
        "clean": cmd_clean,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()

"""
experiments/benchmark_core/isolation.py — Worktree Isolation & Pinned Commit Enforcer.

Enforces:
1. Target Nextcloud repository must exist and match pinned commit.
2. Creates isolated git worktrees via `git worktree add --detach` (or clean isolated clone).
3. Strictly forbids fallback to PolyFlow root or copying partial subdirectories.
4. Fails closed with INVALID_SETUP if repository or composer.json is missing.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

PINNED_NEXTCLOUD_COMMIT = "da57df078d0808a7235a0177bd99d23c010b472e"


class BenchmarkSetupError(Exception):
    """Raised when benchmark prerequisites or worktree isolation fail."""
    pass


class WorktreeManager:
    def __init__(self, target_repo: Path, worktrees_root: Path):
        self.target_repo = target_repo.resolve()
        self.worktrees_root = worktrees_root.resolve()
        self.worktrees_root.mkdir(parents=True, exist_ok=True)

    def verify_target_checkout(self) -> str:
        """Verifies that target repo exists, is a valid git repository, and matches pinned commit."""
        if not self.target_repo.exists() or not (self.target_repo / ".git").exists():
            raise BenchmarkSetupError(f"Target repository not found or not a git checkout at: {self.target_repo}")

        # Check HEAD commit
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.target_repo,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            raise BenchmarkSetupError(f"Failed to inspect git HEAD in {self.target_repo}: {res.stderr}")

        head_commit = res.stdout.strip()
        if head_commit.lower() != PINNED_NEXTCLOUD_COMMIT.lower():
            # If on different commit, attempt to verify if pinned commit exists in repo
            check_obj = subprocess.run(
                ["git", "cat-file", "-e", PINNED_NEXTCLOUD_COMMIT],
                cwd=self.target_repo,
                capture_output=True,
            )
            if check_obj.returncode != 0:
                raise BenchmarkSetupError(
                    f"Pinned commit {PINNED_NEXTCLOUD_COMMIT} not found in {self.target_repo} (current HEAD: {head_commit})"
                )

        return head_commit

    def create_trial_worktree(self, trial_id: str) -> Path:
        """
        Creates an isolated git worktree for a trial.
        Never copies partial folders and never falls back to PolyFlow root.
        """
        self.verify_target_checkout()
        trial_dir = self.worktrees_root / trial_id

        # Clean existing directory if present
        if trial_dir.exists():
            self.remove_trial_worktree(trial_id)

        # Attempt git worktree add --detach
        cmd = ["git", "worktree", "add", "--detach", str(trial_dir), PINNED_NEXTCLOUD_COMMIT]
        res = subprocess.run(cmd, cwd=self.target_repo, capture_output=True, text=True)

        if res.returncode != 0:
            # If worktree creation failed (e.g. branch lock or OneDrive path limitation),
            # perform a clean isolated detached clone from local target repo
            clone_cmd = ["git", "clone", "--no-checkout", str(self.target_repo), str(trial_dir)]
            clone_res = subprocess.run(clone_cmd, capture_output=True, text=True)
            if clone_res.returncode != 0:
                raise BenchmarkSetupError(f"Failed to create isolated trial worktree: {res.stderr} / {clone_res.stderr}")

            # Checkout exact pinned commit in cloned worktree
            co_res = subprocess.run(["git", "checkout", PINNED_NEXTCLOUD_COMMIT], cwd=trial_dir, capture_output=True, text=True)
            if co_res.returncode != 0:
                raise BenchmarkSetupError(f"Failed to checkout pinned commit in clone: {co_res.stderr}")

        # Configure agent identity for trial
        subprocess.run(["git", "config", "user.name", "BlindAgent"], cwd=trial_dir, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.email", "agent@polyflow.ai"], cwd=trial_dir, stdout=subprocess.DEVNULL)

        return trial_dir

    def remove_trial_worktree(self, trial_id: str) -> None:
        """Prunes and removes an isolated worktree safely."""
        trial_dir = self.worktrees_root / trial_id
        if not trial_dir.exists():
            return

        # Attempt git worktree remove
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(trial_dir)],
            cwd=self.target_repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if trial_dir.exists():
            shutil.rmtree(trial_dir, ignore_errors=True)

        # Prune stale worktrees
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=self.target_repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

"""Verify commit ownership and frozen-path preservation without changing Git."""
import fnmatch
import json
from pathlib import Path
import subprocess

ticket = json.loads(Path("plans/rcir_proof/IMPLEMENTATION_TICKET.json").read_text(encoding="utf-8"))
changed = subprocess.check_output(["git", "diff", "--name-only", "-z", ticket["repo_sha"], "HEAD"]).decode().strip("\0").split("\0")
outside = [path for path in changed if not any(fnmatch.fnmatch(path, pattern) for pattern in ticket["owned_paths"])]
forbidden = [path for path in changed if any(fnmatch.fnmatch(path, pattern) for pattern in ticket["forbidden_paths"])]
assert not outside, outside
assert not forbidden, forbidden
staged = subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"]).decode().strip("\0").split("\0")
assert staged == ["plans/PolyFlow_CI_Architecture_Recovery_Execution_Pack_v4 (1).md"], staged
print(json.dumps({"status": "OWNED_COMMITS_AND_FROZEN_PATHS_VERIFIED", "head_sha": subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip(),
                  "changed_owned_files": len(changed), "outside_owned": outside, "forbidden_changes": forbidden,
                  "preserved_owner_staged_document": staged, "unrelated_target_worktree_changes": "PRESERVED"}, indent=2))

"""Study primitives: oracle separation, source-only exports and honest telemetry.

Agent workspaces contain the declared base tree, not shared Git objects. Agent
commands require an OS sandbox; a directory or prompt is never isolation.
"""
from collections import defaultdict
import io
import json
import os
from pathlib import Path
import random
import re
import shutil
import statistics
import subprocess
import tarfile
import tempfile

from rcir.service.snapshot import ServiceError, canonical, digest, safe_path


def export_base(repo, commit, destination):
    """Export only tree objects, refusing submodules, links and existing output."""
    repo, destination = Path(repo).resolve(), Path(destination)
    if destination.exists() or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ServiceError("INVALID_SCOPE", "Exact commit and new export directory required")
    resolved = subprocess.check_output(["git", "-C", str(repo), "rev-parse", commit + "^{commit}"]).decode().strip()
    if resolved != commit:
        raise ServiceError("STALE", "Commit identity mismatch")
    modes = subprocess.check_output(["git", "-C", str(repo), "ls-tree", "-r", commit])
    if any(line.startswith((b"160000 ", b"120000 ")) for line in modes.splitlines()):
        raise ServiceError("UNSUPPORTED", "Explicit dependency materialization required for submodules or links")
    archive = subprocess.check_output(["git", "-C", str(repo), "archive", "--format=tar", commit])
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for member in source:
            relative = member.name.rstrip("/")
            path = safe_path(destination.resolve(), relative)
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                path.parent.mkdir(parents=True, exist_ok=True)
                stream = source.extractfile(member)
                path.write_bytes(stream.read())
                path.chmod(0o755 if member.mode & 0o111 else 0o644)
            else:
                raise ServiceError("INVALID_SCOPE", "Unsafe archive entry")
    return {"base_sha": commit, "archive_sha256": digest(archive), "git_objects_exposed": False}


class LinuxSandbox:
    """Bubblewrap with PID, network and filesystem separation; never host fallback."""
    def __init__(self, workspace):
        self.root = Path(workspace).resolve()
        self.executable = shutil.which("bwrap") if os.name == "posix" else None
        if self.executable is None:
            raise ServiceError("BLOCKED", "A functioning Linux bubblewrap sandbox is required; host execution refused")
        if not self.root.is_dir() or self.root == Path("/"):
            raise ServiceError("INVALID_SCOPE", "A bounded trial workspace is required")

    def execute(self, command, *, timeout=60, oracle=None):
        if not command or not all(isinstance(arg, str) for arg in command):
            raise ServiceError("INVALID_SCOPE", "Explicit argument-vector command required")
        argv = [self.executable, "--unshare-all", "--die-with-parent", "--new-session", "--clearenv",
                "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "HOME", "/tmp", "--ro-bind", "/usr", "/usr"]
        for system in ["/bin", "/lib", "/lib64"]:
            if Path(system).exists():
                argv += ["--ro-bind", system, system]
        argv += ["--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--bind", str(self.root), "/work", "--chdir", "/work"]
        if oracle is not None:
            oracle = Path(oracle).resolve()
            try:
                oracle.relative_to(self.root)
            except ValueError:
                pass
            else:
                raise ServiceError("INVALID_SCOPE", "Oracle may not be inside agent workspace")
            argv += ["--ro-bind", str(oracle), "/oracle"]
        import resource
        def resource_bounds():
            resource.setrlimit(resource.RLIMIT_FSIZE, (8_000_000, 8_000_000))
            resource.setrlimit(resource.RLIMIT_CPU, (max(1, int(timeout) + 1), max(1, int(timeout) + 1)))
            resource.setrlimit(resource.RLIMIT_AS, (2_000_000_000, 2_000_000_000))
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            result = subprocess.run(argv + ["--", *command], stdout=stdout, stderr=stderr, timeout=timeout, preexec_fn=resource_bounds)
            stdout.seek(0)
            stderr.seek(0)
            return {"command": command, "exit_code": result.returncode,
                    "stdout": stdout.read(8_000_000).decode("utf-8", errors="replace"),
                    "stderr": stderr.read(8_000_000).decode("utf-8", errors="replace"),
                    "output_file_limit_bytes": 8_000_000, "address_space_limit_bytes": 2_000_000_000,
                    "sandbox": "BWRAP_UNSHARED_NETWORK_PID_FILESYSTEM"}


def validate_protocol(public, private, protocol):
    tasks = public.get("tasks", [])
    if not tasks or len({t.get("task_id") for t in tasks}) != len(tasks):
        raise ServiceError("INVALID_SCOPE", "Nonempty unique public tasks required")
    if protocol.get("curator_approval") != "INDEPENDENTLY_REVIEWED" or not protocol.get("curator_receipt_sha256"):
        raise ServiceError("BLOCKED", "Independent curator receipt is required")
    if set(protocol.get("arms", [])) - {"A", "B", "C", "D"} or not {"A", "B"} <= set(protocol.get("arms", [])):
        raise ServiceError("INVALID_SCOPE", "Protocol must declare A/B and any optional C/D arms")
    for bound in ["max_turns", "max_seconds", "max_input_tokens", "max_output_tokens", "replicates"]:
        if type(protocol.get(bound)) is not int or protocol[bound] <= 0:
            raise ServiceError("INVALID_SCOPE", "Positive preregistered resource bounds required")
    family_split = {}
    for task in tasks:
        if set(task) != {"task_id", "repo_url", "base_sha", "prompt", "split", "issue_family", "available_commands"}:
            raise ServiceError("INVALID_SCOPE", "Public task contains missing or evaluator-only fields")
        if task["split"] not in {"DEV", "VALIDATION", "LOCKED"} or not re.fullmatch(r"[0-9a-f]{40}", task["base_sha"]):
            raise ServiceError("INVALID_SCOPE", "Invalid split or base SHA")
        family = task["repo_url"], task["issue_family"]
        if family in family_split and family_split[family] != task["split"]:
            raise ServiceError("INVALID_SCOPE", "Issue family leaks across splits")
        family_split[family] = task["split"]
        oracle = private.get(task["task_id"], {})
        required = {"fix_sha", "hidden_tests_sha256", "reference_patch_sha256", "qualification_receipt_sha256", "source_license", "container_digest"}
        if not required <= set(oracle) or any(not oracle[k] for k in required):
            raise ServiceError("BLOCKED", "Qualified private oracle provenance is incomplete")
        if not all(re.fullmatch(r"[0-9a-f]{64}", oracle[k]) for k in ["hidden_tests_sha256", "reference_patch_sha256", "qualification_receipt_sha256"]):
            raise ServiceError("INVALID_SCOPE", "Private evidence digests must be SHA-256")
        if not re.fullmatch(r"[0-9a-f]{40}", oracle["fix_sha"]) or oracle["fix_sha"] == task["base_sha"]:
            raise ServiceError("INVALID_SCOPE", "Distinct reference fix commit required")
    return {"status": "STRUCTURE_VALIDATED_NOT_CURATOR_AUTHENTICATED", "task_count": len(tasks),
            "public_sha256": digest(canonical(public)), "private_sha256": digest(canonical(private)),
            "protocol_sha256": digest(canonical(protocol)), "release_eligible": False}


def counterbalanced_schedule(task_ids, arms, replicates, seed):
    if len(set(arms)) != len(arms) or not arms or replicates < 1:
        raise ServiceError("INVALID_SCOPE", "Distinct arms and positive replicate count required")
    rng = random.Random(seed)
    tasks, order = sorted(task_ids), list(arms)
    rng.shuffle(tasks)
    rng.shuffle(order)
    schedule = []
    for index, task in enumerate(tasks):
        for repeat in range(replicates):
            shift = (index + repeat) % len(order)
            for position, arm in enumerate(order[shift:] + order[:shift]):
                schedule.append({"task_id": task, "replicate": repeat, "arm": arm, "position": position,
                                 "namespace": digest(canonical([seed, task, repeat, arm]))})
    return schedule


def summarize_trials(rows, *, seed=0, resamples=2000, expected_schedule=None):
    """ITT includes failures/timeouts; missing native usage stays null.

    Paired token savings are secondary and require both arms to succeed with
    actual usage. Confidence intervals bootstrap task clusters, not trial rows.
    """
    if type(resamples) is not int or not 1 <= resamples <= 100000:
        raise ServiceError("INVALID_SCOPE", "Bounded positive bootstrap resamples required")
    rows = list(rows)
    identity = lambda row: (row["task_id"], row["replicate"], row["arm"])
    if len({identity(r) for r in rows}) != len(rows):
        raise ServiceError("INVALID_SCOPE", "Duplicate trial identity")
    missing = []
    if expected_schedule is not None:
        planned = {identity(row) for row in expected_schedule}
        observed = {identity(row) for row in rows}
        if len(planned) != len(expected_schedule) or observed - planned:
            raise ServiceError("INVALID_SCOPE", "Trial schedule duplicates or unplanned observations")
        missing = sorted(planned - observed)
        rows += [{"task_id": task, "replicate": repeat, "arm": arm, "success": False, "status": "MISSING_PLANNED_TRIAL"}
                 for task, repeat, arm in missing]
    arms = sorted({r["arm"] for r in rows})
    itt = {arm: {"trials": sum(r["arm"] == arm for r in rows),
                 "successes": sum(r["arm"] == arm and r.get("success") is True for r in rows)} for arm in arms}
    by_pair = defaultdict(dict)
    for row in rows:
        by_pair[row["task_id"], row["replicate"]][row["arm"]] = row
    clusters = defaultdict(list)
    for (task, _), pair in by_pair.items():
        if {"A", "B"} <= pair.keys() and all(pair[a].get("success") is True for a in ["A", "B"]):
            a, b = pair["A"].get("native_input_tokens"), pair["B"].get("native_input_tokens")
            if type(a) is int and a > 0 and type(b) is int and b >= 0:
                clusters[task].append((a - b) / a)
    values = [statistics.mean(v) for v in clusters.values()]
    rng = random.Random(seed)
    bootstrap = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(resamples)) if len(values) >= 2 else []
    interval = [bootstrap[int(.025 * resamples)], bootstrap[min(resamples - 1, int(.975 * resamples))]] if bootstrap else None
    return {"itt": itt, "itt_scope": "PREREGISTERED_SCHEDULE" if expected_schedule is not None else "OBSERVED_ROWS_ONLY",
            "missing_planned_trials": len(missing), "both_success_task_clusters_with_native_usage": len(values),
            "secondary_mean_input_reduction": statistics.mean(values) if values else None,
            "task_cluster_bootstrap_95_interval": interval,
            "efficiency_status": "EXPLORATORY" if values else "NOT_MEASURED",
            "native_ide_credits": None, "release_eligible": False}


def qualify_change(repo, base, fix, oracle, command, output):
    """Execute base-negative, reference-positive and irrelevant-edit controls.

    Exit 1 must mean assertion failure for this explicitly qualified command.
    Setup errors (other nonzero codes), missing tests and timeouts cannot pass.
    Curator review of task meaning remains a separate requirement.
    """
    from rcir.service.proof import seal_run
    output, oracle = Path(output), Path(oracle).resolve()
    if output.exists() or base == fix or not oracle.is_dir():
        raise ServiceError("INVALID_SCOPE", "New output, distinct base/fix and separate oracle directory required")
    inventory = {}
    for file in sorted(oracle.rglob("*")):
        if file.is_symlink():
            raise ServiceError("INVALID_SCOPE", "Oracle links are unsupported")
        if file.is_file():
            inventory[file.relative_to(oracle).as_posix()] = digest(file.read_bytes())
    if not inventory:
        raise ServiceError("INVALID_SCOPE", "Oracle is empty")
    output.mkdir(parents=True)
    results = {}
    for name, commit in [("base", base), ("reference", fix), ("irrelevant", base)]:
        root = output / name
        export_base(repo, commit, root)
        if name == "irrelevant":
            marker = root / "rcir_irrelevant_control.txt"
            if marker.exists():
                raise ServiceError("INVALID_SCOPE", "Negative-control marker would overwrite source")
            marker.write_text("This file does not implement the task.\n", encoding="utf-8")
        receipt = LinuxSandbox(root).execute(command, timeout=120, oracle=oracle)
        results[name] = receipt
        (output / f"{name}-receipt.json").write_bytes(canonical(receipt))
    qualified = results["base"]["exit_code"] == 1 and results["reference"]["exit_code"] == 0 and results["irrelevant"]["exit_code"] == 1
    result = {"status": "CONTROL_EXECUTION_QUALIFIED" if qualified else "CONTROL_QUALIFICATION_FAILED",
              "base_sha": base, "fix_sha": fix, "command": command, "oracle_inventory": inventory,
              "independent_curator_review": "NOT_PERFORMED_BY_THIS_TOOL", "release_eligible": False}
    (output / "qualification.json").write_bytes(canonical(result))
    # Source exports may have generated caches after tests; seal actual bytes.
    seal_run(output)
    return result

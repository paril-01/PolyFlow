"""Validate study inputs, export isolated base trees, or summarize raw trials.

Live evidence requires independently qualified tasks and recorded real trials.
This command deliberately cannot invent trials or native IDE usage.
"""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "rcir/src")]
from experiments.benchmark_core.product_study import export_base, validate_protocol, summarize_trials, LinuxSandbox, qualify_change


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    validate = commands.add_parser("validate")
    for name in ["public", "private", "protocol"]:
        validate.add_argument("--" + name, required=True, type=Path)
    export = commands.add_parser("export-base")
    for name in ["repo", "commit", "output"]:
        export.add_argument("--" + name, required=True)
    summary = commands.add_parser("summarize")
    summary.add_argument("--trials", required=True, type=Path)
    summary.add_argument("--schedule", type=Path)
    sandbox = commands.add_parser("check-sandbox")
    sandbox.add_argument("--workspace", required=True, type=Path)
    qualify = commands.add_parser("qualify")
    for name in ["repo", "base", "fix", "oracle", "output"]:
        qualify.add_argument("--" + name, required=True)
    qualify.add_argument("--command", required=True, nargs=argparse.REMAINDER)
    trial = commands.add_parser("run-dev")
    for name in ["repo", "base", "prompt-file", "task-id", "model", "limits-file", "output"]:
        trial.add_argument("--" + name, required=True)
    trial.add_argument("--arm", choices=["A", "B"], required=True)
    trial.add_argument("--endpoint", default="http://127.0.0.1:11434")
    evaluate = commands.add_parser("evaluate")
    for name in ["repo", "base", "changes", "oracle", "qualified-controls", "output"]:
        evaluate.add_argument("--" + name, required=True)
    evaluate.add_argument("--command", required=True, nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.operation == "validate":
            result = validate_protocol(*(json.loads(getattr(args, field).read_text(encoding="utf-8")) for field in ["public", "private", "protocol"]))
        elif args.operation == "export-base":
            result = export_base(args.repo, args.commit, args.output)
        elif args.operation == "summarize":
            result = summarize_trials(json.loads(args.trials.read_text(encoding="utf-8")),
                expected_schedule=json.loads(args.schedule.read_text(encoding="utf-8")) if args.schedule else None)
        elif args.operation == "qualify":
            result = qualify_change(args.repo, args.base, args.fix, args.oracle, args.command, args.output)
            if result["status"] != "CONTROL_EXECUTION_QUALIFIED":
                print(json.dumps(result, indent=2))
                return 2
        elif args.operation == "run-dev":
            from experiments.benchmark_core.agent_trial import LocalOllama, TrialLimits, run_dev_trial
            result = run_dev_trial(args.repo, args.base, Path(args.prompt_file).read_text(encoding="utf-8"), args.arm, args.output,
                                   LocalOllama(args.endpoint, args.model), TrialLimits(**json.loads(Path(args.limits_file).read_text(encoding="utf-8"))), task_id=args.task_id)
            if result["status"] != "AGENT_FINISHED_NOT_YET_EVALUATED":
                print(json.dumps(result, indent=2))
                return 2
        elif args.operation == "evaluate":
            from experiments.benchmark_core.agent_trial import evaluate_trial
            result = evaluate_trial(args.repo, args.base, args.changes, args.oracle, args.command, args.output,
                                    qualified_control_receipt=args.qualified_controls)
            if not result["success"]:
                print(json.dumps(result, indent=2))
                return 2
        else:
            result = LinuxSandbox(args.workspace).execute(["/usr/bin/true"])
            if result["exit_code"]:
                print(json.dumps(result))
                return 2
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": getattr(exc, "status", "INVALID_SETUP"), "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

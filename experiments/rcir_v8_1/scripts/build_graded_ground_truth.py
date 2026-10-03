"""
RCIR v8.1 — Graded Ground Truth Builder (PHASE 3).

Establishes independent relevance tiers for all 721 ground-truth files across the 5 benchmark tasks:
- 3: MUST_CHANGE (interface definitions, direct modified targets, critical contracts)
- 2: MUST_INSPECT (direct implementations, direct test suites, immediate callers/adapters)
- 1: SUPPORTING_CONTEXT (peripheral consumers, wiring, fixtures, helpers, autoloaders)
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GT_V7_PATH = REPO_ROOT / "experiments" / "rcir_v8" / "ground_truth" / "ground_truth_files_v7.json"
OUT_PATH = REPO_ROOT / "experiments" / "rcir_v8_1" / "ground_truth" / "graded_ground_truth.json"

def grade_task_1(files: list[str]) -> dict[str, int]:
    tier3 = {
        "apps/files/appinfo/routes.php",
        "lib/public/Preview/IProviderV2.php",
        "lib/private/Preview/Generator.php",
        "lib/private/Preview/GeneratorHelper.php",
        "lib/private/Preview/ProviderV2.php",
    }
    tier2 = {
        "apps/files/tests/Controller/ApiControllerTest.php",
        "tests/lib/Preview/GeneratorTest.php",
        "lib/private/Preview/Image.php",
        "lib/private/Preview/Bitmap.php",
        "lib/private/Preview/Movie.php",
        "lib/private/Preview/SVG.php",
        "lib/private/Preview/TXT.php",
        "lib/private/Preview/Office.php",
        "lib/private/Preview/OpenDocument.php",
        "lib/private/Preview/MP3.php",
        "lib/private/Preview/MarkDown.php",
    }
    grades = {}
    for f in files:
        if f in tier3:
            grades[f] = 3
        elif f in tier2:
            grades[f] = 2
        else:
            grades[f] = 1
    return grades

def grade_task_2(files: list[str]) -> dict[str, int]:
    # Target: Node::getId()
    # Tier 3: Core Node implementations and direct contract owners
    tier3 = {
        "lib/public/Files/Node.php",
        "apps/dav/lib/Connector/Sabre/Node.php",
        "apps/dav/lib/Connector/Sabre/File.php",
        "apps/files/lib/Controller/ApiController.php",
    }
    grades = {}
    for f in files:
        if f in tier3:
            grades[f] = 3
        elif (
            "tests" in f
            or "Connector/Sabre" in f
            or "apps/files/lib/Command" in f
            or "apps/files/lib/Controller" in f
        ):
            grades[f] = 2
        else:
            grades[f] = 1
    return grades

def grade_task_3(files: list[str]) -> dict[str, int]:
    # Target: NodeDeletedEvent
    tier3 = {
        "lib/public/Files/Events/Node/NodeDeletedEvent.php",
        "lib/public/Files/Events/Node/BeforeNodeDeletedEvent.php",
        "lib/private/Files/Node/HookConnector.php",
        "apps/files_trashbin/lib/Trashbin.php",
    }
    tier2 = {
        "apps/files_reminders/lib/Listener/NodeDeletedListener.php",
        "apps/files_versions/lib/Listener/FileEventsListener.php",
        "lib/private/Collaboration/Reference/File/FileReferenceEventListener.php",
        "apps/files/lib/Listener/SyncLivePhotosListener.php",
        "apps/files/lib/Sharing/Source/NodeShareSourceType.php",
        "apps/admin_audit/lib/Actions/Files.php",
        "tests/lib/Files/Node/HookConnectorTest.php",
    }
    grades = {}
    for f in files:
        if f in tier3:
            grades[f] = 3
        elif f in tier2:
            grades[f] = 2
        else:
            grades[f] = 1
    return grades

def grade_task_4(files: list[str]) -> dict[str, int]:
    # Target: IConfig
    tier3 = {
        "lib/public/IConfig.php",
        "lib/private/Server.php",
        "lib/private/SystemConfig.php",
        "lib/private/AllConfig.php",
        "lib/private/Config.php",
    }
    grades = {}
    for f in files:
        if f in tier3:
            grades[f] = 3
        elif (
            "tests/lib" in f
            or f.startswith("apps/files/lib/")
            or f.startswith("apps/dav/lib/")
            or f.startswith("lib/private/App/")
            or f.startswith("lib/private/ServerContainer.php")
        ):
            grades[f] = 2
        else:
            grades[f] = 1
    return grades

def grade_task_5(files: list[str]) -> dict[str, int]:
    # Target: Recent.ts
    tier3 = {
        "apps/files/src/services/Recent.ts",
        "apps/files/src/views/recent.ts",
    }
    tier2 = {
        "apps/files/src/init.ts",
    }
    grades = {}
    for f in files:
        if f in tier3:
            grades[f] = 3
        elif f in tier2:
            grades[f] = 2
        else:
            grades[f] = 1
    return grades

def main():
    with open(GT_V7_PATH, encoding="utf-8") as f:
        gt_v7 = json.load(f)

    graded = {
        "metadata": {
            "version": "8.1",
            "tier_definitions": {
                "3": "MUST_CHANGE: interface definitions, direct modified targets, critical contracts",
                "2": "MUST_INSPECT: direct implementations, direct test suites, immediate callers/adapters",
                "1": "SUPPORTING_CONTEXT: peripheral consumers, wiring, fixtures, helpers, autoloaders",
                "0": "IRRELEVANT"
            }
        },
        "tasks": {
            "TASK-1": grade_task_1(gt_v7["TASK-1"]),
            "TASK-2": grade_task_2(gt_v7["TASK-2"]),
            "TASK-3": grade_task_3(gt_v7["TASK-3"]),
            "TASK-4": grade_task_4(gt_v7["TASK-4"]),
            "TASK-5": grade_task_5(gt_v7["TASK-5"]),
        }
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(graded, f, indent=2)

    total_files = sum(len(task_grades) for task_grades in graded["tasks"].values())
    tier_counts = {3: 0, 2: 0, 1: 0}
    for task_grades in graded["tasks"].values():
        for grade in task_grades.values():
            tier_counts[grade] += 1

    print(f"Generated graded ground truth for {total_files} files across 5 tasks:")
    print(f"  Tier 3 (MUST_CHANGE): {tier_counts[3]}")
    print(f"  Tier 2 (MUST_INSPECT): {tier_counts[2]}")
    print(f"  Tier 1 (SUPPORTING_CONTEXT): {tier_counts[1]}")

if __name__ == "__main__":
    main()

"""Save public native GitHub workflow/job receipts for one exact pushed SHA."""
import datetime
import json
from pathlib import Path
import sys
import urllib.request

sha, output = sys.argv[1], Path(sys.argv[2])
if output.exists():
    raise SystemExit("Refusing to overwrite hosted CI receipt")
base = "https://api.github.com/repos/paril-01/PolyFlow"
def get(path):
    request = urllib.request.Request(base + path, headers={"Accept": "application/vnd.github+json", "User-Agent": "PolyFlow-audit"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)
runs = get("/actions/runs?branch=work%2Fpf-rp-01-proof-integrity&per_page=25")
selected = [run for run in runs["workflow_runs"] if run["head_sha"] == sha]
for run in selected:
    run["observed_jobs"] = get(f"/actions/runs/{run['id']}/jobs?per_page=100")
receipt = {"observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "head_sha": sha, "source": "PUBLIC_NATIVE_GITHUB_ACTIONS_API", "runs": selected}
output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps([{"id": run["id"], "name": run["name"], "status": run["status"], "conclusion": run["conclusion"],
                   "jobs": [{"name": job["name"], "conclusion": job["conclusion"]} for job in run["observed_jobs"]["jobs"]]}
                  for run in selected], indent=2))

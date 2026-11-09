"""Post (or update) one plain PR comment with pytest results. Stdlib only.

python3 .github/scripts/test_comment.py Play pytest-results.xml            # in a pull_request job
python3 .github/scripts/test_comment.py Play pytest-results.xml --dry-run  # print the body
Env: GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER, HEAD_SHA, RUN_URL (GITHUB_API_URL optional).
"""

import argparse
import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

MAX_FAILURES = 10
MAX_LINES = 15


def summarize(xml_path: Path) -> tuple[dict, list[tuple[str, str]]]:
    """Totals and [(test id, short error)] from a pytest --junitxml file."""
    root = ET.parse(xml_path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}
    for s in suites:
        for k in totals:
            totals[k] += float(s.get(k, 0)) if k == "time" else int(s.get(k, 0))
    failed = []
    for case in root.iter("testcase"):
        problem = case.find("failure")
        if problem is None:
            problem = case.find("error")
        if problem is None:
            continue
        test_id = f"{case.get('classname', '')}::{case.get('name', '')}".lstrip(":")
        text = (problem.text or problem.get("message") or "").strip()
        lines = text.splitlines()
        short = "\n".join(lines[-MAX_LINES:])  # pytest puts the assertion at the end
        failed.append((test_id, short))
    return totals, failed


def render(name: str, marker: str, xml_path: Path, head_sha: str, run_url: str) -> str:
    meta = " · ".join(
        x
        for x in (
            f"`{head_sha[:7]}`" if head_sha else "",
            f"[run]({run_url})" if run_url else "",
        )
        if x
    )
    if not xml_path.exists():
        return f"{marker}\n**{name} tests: ⚠️ did not run** (an earlier step failed){f' · {meta}' if meta else ''}\n"

    t, failed = summarize(xml_path)
    bad = t["failures"] + t["errors"]
    passed = t["tests"] - bad - t["skipped"]
    counts = (
        ", ".join(
            f"{n} {label}"
            for n, label in (
                (bad, "failed"),
                (passed, "passed"),
                (t["skipped"], "skipped"),
            )
            if n
        )
        or "no tests"
    )
    status = "❌" if bad else "✅"
    parts = [
        f"{marker}\n**{name} tests: {status} {counts}** in {t['time']:.1f}s"
        + (f" · {meta}" if meta else "")
    ]
    for test_id, short in failed[:MAX_FAILURES]:
        parts.append(
            f"<details><summary><code>{test_id}</code></summary>\n\n```text\n{short}\n```\n</details>"
        )
    if len(failed) > MAX_FAILURES:
        parts.append(f"…and {len(failed) - MAX_FAILURES} more, see the run.")
    return "\n\n".join(parts) + "\n"


def api(method: str, path: str, body: dict | None = None):
    base = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    req = urllib.request.Request(
        base + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def upsert(repo: str, pr: str, marker: str, body: str) -> str:
    """Update our earlier comment (found by its hidden marker) or create one."""
    page = 1
    while comments := api(
        "GET", f"/repos/{repo}/issues/{pr}/comments?per_page=100&page={page}"
    ):
        for c in comments:
            if c["body"].startswith(marker):
                api("PATCH", f"/repos/{repo}/issues/comments/{c['id']}", {"body": body})
                return "updated"
        page += 1
    api("POST", f"/repos/{repo}/issues/{pr}/comments", {"body": body})
    return "created"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("name", help="label, e.g. Play")
    p.add_argument("junit_xml", type=Path)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    marker = f"<!-- test-comment:{args.name.lower()} -->"
    body = render(
        args.name,
        marker,
        args.junit_xml,
        os.environ.get("HEAD_SHA", ""),
        os.environ.get("RUN_URL", ""),
    )
    if args.dry_run:
        print(body)
        return
    result = upsert(
        os.environ["GITHUB_REPOSITORY"], os.environ["PR_NUMBER"], marker, body
    )
    print(f"Comment {result}:\n{body}")


if __name__ == "__main__":
    main()

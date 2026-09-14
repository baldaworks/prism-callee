#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

python3 - "$repo_root" <<'PY'
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1]).resolve()
failures = []


def record(condition: bool, message: str) -> None:
    if condition:
        print(f"PASS: {message}")
    else:
        print(f"FAIL: {message}", file=sys.stderr)
        failures.append(message)


def read(relative: str) -> str:
    path = root / relative
    record(path.is_file(), f"{relative} exists")
    return path.read_text() if path.is_file() else ""



documents = {relative: read(relative) for relative in ["README.md","docs/architecture-callee-lifecycle.md","docs/callee-lifecycle-smoke-test.md"]}
readme = documents["README.md"]
plugin_name = "prism-callee"
marketplace = json.loads(read(".agents/plugins/marketplace.json"))
record([p.get("name") for p in marketplace.get("plugins", [])] == [plugin_name], "marketplace contains only its own plugin")
record(marketplace.get("name") == plugin_name, "marketplace identity matches repository")
for marker in ["$prism-callee:lifecycle","/prism-callee:lifecycle","/prism-callee-lifecycle"]:
    record(marker in readme, f"README documents public entrypoint {marker}")
record(f"${plugin_name}:lifecycle Add CSV export to the report page." in readme, f"README shows a free-form request for ${plugin_name}:lifecycle")
for marker in ["ROUTE=story", "ITEM_ID=", "ITEM_TYPE=", "BEADS_CONTEXT:", "callee agent run prism/lifecycle"]:
    record(marker not in readme, f"README hides internal Callee protocol: {marker}")
required_links = ["https://github.com/baldaworks/prism","https://github.com/baldaworks/prism/blob/main/plugins/prism/skills/lifecycle/SKILL.md","https://github.com/baldaworks/prism/blob/main/plugins/prism/skills/story/SKILL.md","https://github.com/baldaworks/prism/blob/main/plugins/prism/skills/epic/SKILL.md"]
readme_links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme)
for target in required_links:
    record(target in readme_links, f"mandatory cross-link: {target}")
for marker in ["./scripts/validate-documentation.sh", "./scripts/test-documentation-drift-detection.sh"]:
    record(marker in readme, f"README lists documentation check {marker}")
for relative, text in documents.items():
    record("callee agent import baldaworks/prism " not in text, f"{relative} excludes old Callee import source")
callee_doc = documents["docs/architecture-callee-lifecycle.md"]
record("`callee` `0.19.0`" in readme, "README documents the Callee 0.19.0 baseline")
for relative in ["README.md", "docs/architecture-callee-lifecycle.md", "docs/callee-lifecycle-smoke-test.md"]:
    text = documents[relative]
    for marker in [
        "callee agent import baldaworks/prism-callee",
        "--path pack/callee/prism",
        "--prefix prism",
        "--force",
        "callee agent view prism/lifecycle --json",
        "callee agent view prism/story --json",
        "callee agent view prism/epic --json",
    ]:
        record(marker in text, f"{relative} documents Callee catalog operation: {marker}")
    normalized = " ".join(text.replace("\\\n", " ").split())
    force_import = "callee agent import baldaworks/prism-callee --path pack/callee/prism --prefix prism --force"
    record(force_import in normalized, f"{relative} contains the executable Callee force-import command")

for marker in ["kind `Router`", "stale", "Sequential"]:
    record(marker in callee_doc, f"Callee architecture documents catalog invariant: {marker}")
for marker in [
    "## Public UX and internal runtime",
    "## Internal runner ABI",
    "not the public Prism Callee UX",
]:
    record(marker in callee_doc, f"Callee architecture marks the runner boundary: {marker}")

smoke_doc = documents["docs/callee-lifecycle-smoke-test.md"]
for marker in ["pack-level test entrypoints", "not the public free-form plugin UX"]:
    record(marker in smoke_doc, f"Callee smoke test keeps pack internals maintainer-only: {marker}")

pack_lifecycle = read("pack/callee/prism/lifecycle.md")
record("kind: Router" in pack_lifecycle, "checked-in prism/lifecycle is a Router")
record((root / "pack/callee/prism/story.md").is_file(), "checked-in prism/story root exists")
record((root / "pack/callee/prism/epic.md").is_file(), "checked-in prism/epic root exists")


diagram_minimums = {"README.md":1,"docs/architecture-callee-lifecycle.md":1}
for relative, minimum in diagram_minimums.items():
    blocks = re.findall(r"```mermaid\s*\n(.*?)```", documents[relative], flags=re.DOTALL)
    record(len(blocks) >= minimum, f"{relative} has at least {minimum} Mermaid lifecycle diagram(s)")
    record(all(block.lstrip().startswith("flowchart TB") for block in blocks), f"{relative} keeps Mermaid diagrams vertical")

link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
for relative, text in documents.items():
    source = root / relative
    for raw_target in link_pattern.findall(text):
        target = raw_target.strip().strip("<>")
        if target.startswith(("http://", "https://", "mailto:", "codex://", "#")):
            continue
        file_target = target.split("#", 1)[0]
        if not file_target:
            continue
        resolved = (source.parent / file_target).resolve()
        record(resolved.exists(), f"{relative} local link resolves: {target}")

if failures:
    print(f"\nDocumentation validation failed with {len(failures)} finding(s).", file=sys.stderr)
    raise SystemExit(1)

print("\nPASS: documentation contracts are current")
PY

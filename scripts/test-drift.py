"""Exercise validators against isolated copies of the current working tree."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

root = pathlib.Path(sys.argv[1]).resolve()
kind = sys.argv[2]
plugin = "prism-callee"
validator = "validate-documentation.sh" if kind == "documentation" else "validate-lifecycle-ownership.sh"

def validate(path):
    return subprocess.run(["bash", str(path / "scripts" / validator), str(path)],
                          cwd=path, capture_output=True, text=True, check=False)

def refresh_digests(path, section_name):
    mapping_path = path / "docs/lifecycle-ownership.json"
    mapping = json.loads(mapping_path.read_text())
    section = mapping["integrity"][section_name]
    anchor = path / section.get("root", "")
    digest = hashlib.sha256()
    for item in section["sources"]:
        data = (anchor / item["path"]).read_bytes()
        item["sha256"] = hashlib.sha256(data).hexdigest()
        digest.update(item["path"].encode() + b"\0" + data + b"\0")
    section["aggregate_sha256"] = digest.hexdigest()
    mapping_path.write_text(json.dumps(mapping, indent=2) + "\n")

with tempfile.TemporaryDirectory(prefix="prism-drift-") as temporary:
    temp = pathlib.Path(temporary)
    baseline = temp / "baseline"
    shutil.copytree(root, baseline, ignore=shutil.ignore_patterns(
        ".git", ".beads", ".dolt", ".callee", "__pycache__"))
    result = validate(baseline)
    assert result.returncode == 0, result.stdout + result.stderr
    print("PASS: isolated working-tree baseline validates")
    cases = []
    if kind == "documentation":
        targets = ["https://github.com/baldaworks/prism","https://github.com/baldaworks/prism/blob/main/plugins/prism/skills/lifecycle/SKILL.md","https://github.com/baldaworks/prism/blob/main/plugins/prism/skills/story/SKILL.md","https://github.com/baldaworks/prism/blob/main/plugins/prism/skills/epic/SKILL.md","CONTRIBUTING.md","pack/callee/prism/lifecycle.md","pack/callee/prism/story.md","pack/callee/prism/epic.md"]
        for target in targets:
            for replacement in ["", "https://example.invalid/wrong"]:
                cases.append(("README.md", "(" + target + ")", "(" + replacement + ")",
                              "FAIL: mandatory cross-link: " + target))
        cases.extend([
            ("README.md", f"${plugin}:lifecycle Add CSV export to the report page.",
             f"${plugin}:lifecycle", "FAIL: README shows a free-form request"),
            ("README.md", "## Quick start", "ROUTE=story\n\n## Quick start",
             "FAIL: README hides internal Callee protocol: ROUTE=story"),
            ("README.md", "## Learn more", "## Ownership and validation\n\n## Learn more",
             "FAIL: README excludes maintenance policy: ## Ownership and validation"),
            ("README.md", "## License", "## Authority and license",
             "FAIL: README has a plain License section"),
            ("README.md", "## Learn more", "./scripts/validate-documentation.sh\n\n## Learn more",
             "FAIL: README excludes maintenance check ./scripts/validate-documentation.sh"),
            ("CONTRIBUTING.md", "./scripts/validate-documentation.sh", "",
             "FAIL: CONTRIBUTING lists maintenance check ./scripts/validate-documentation.sh"),
            ("CONTRIBUTING.md", "./scripts/test-documentation-drift-detection.sh", "",
             "FAIL: CONTRIBUTING lists maintenance check ./scripts/test-documentation-drift-detection.sh"),
            ("README.md", 'callee agent run prism/story --message "Add CSV export to the report page."',
             'callee agent run prism/story "Add CSV export to the report page."',
             "FAIL: README documents the complete Story workflow command"),
            ("README.md", 'callee agent run prism/epic --message "Coordinate CSV export across reporting services."',
             'callee agent run prism/epic "Coordinate CSV export across reporting services."',
             "FAIL: README documents the complete Epic workflow command"),
            ("README.md", "resolve a Beads item", "choose a target",
             "FAIL: README documents the direct-run persistence boundary: resolve a Beads item"),
            ("README.md", "## Workflows", "callee agent run prism/roles/story-specifier\n\n## Workflows",
             "FAIL: README excludes standalone internal role command: callee agent run prism/roles/"),
            ("README.md", "(LICENSE)", "(missing-license)", "FAIL: README.md local link resolves: missing-license"),
            ("docs/architecture-callee-lifecycle.md",
             "flowchart TB", "flowchart LR", "keeps Mermaid diagrams vertical"),
        ])
        cases.extend([
            ("README.md", "`callee` `0.19.0`", "`callee` `0.18.0`", "FAIL: README documents the Callee 0.19.0 baseline"),
            ("docs/architecture-callee-lifecycle.md", "  --force", "  --debug", "contains the executable Callee force-import command"),
            ("docs/architecture-callee-lifecycle.md", "## Internal runner ABI", "## Direct execution", "marks the runner boundary: ## Internal runner ABI"),
        ])

    else:
        cases.extend([
            ("plugins/prism-callee/skills/lifecycle/SKILL.md",
             "Require all three imported roots", "silently bypass this step",
             "FAIL: host source digest matches:"),
            ("plugins/prism-callee/prefixed-skills/prism-callee-lifecycle/SKILL.md",
             "Require all three imported roots", "silently bypass this step",
             "FAIL: callee_lifecycle mirror matches: SKILL.md"),
        ])
        cases.append(("pack/callee/prism/phases/breakdown.md",
                      "There is no numeric minimum or", "Use a fixed child count; there is no",
                      "FAIL: Callee pack source digest matches: prism/phases/breakdown.md"))
        synchronized = temp / "synchronized"
        shutil.copytree(baseline, synchronized)
        path = synchronized / "pack/callee/prism/phases/breakdown.md"
        before = path.read_text()
        after = before.replace("explicit dependencies", "necessary explicit dependencies")
        assert after != before
        path.write_text(after)
        refresh_digests(synchronized, "callee_pack")
        result = validate(synchronized)
        assert result.returncode == 0, result.stdout + result.stderr
        print("PASS: synchronized pack evolution validates")

    for index, (relative, old, new, expected) in enumerate(cases):
        mutant = temp / str(index)
        shutil.copytree(baseline, mutant)
        path = mutant / relative
        before = path.read_text()
        assert old in before, (relative, old)
        path.write_text(before.replace(old, new))
        result = validate(mutant)
        output = result.stdout + result.stderr
        assert result.returncode != 0 and expected in output, (relative, expected, output)
        print(f"PASS: rejects mutation {index + 1}: {relative}")
print(f"PASS: {kind} drift-detection fixtures")

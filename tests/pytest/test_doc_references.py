"""Markdown reference gate (tuna-os/tromso#511, approved in #467).

Stale paths in README.md / AGENTS.md / docs drifted from the code once already
(the build-log paths, fixed in #512). This keeps them honest:

* backticked repo-relative paths and relative Markdown links in tracked `*.md`
  files must point at something that exists;
* every `tromso-build.log` path in README.md and AGENTS.md must equal the
  `LOG=` value in just/buildstream.just.

Pure source inspection: no network, stdlib only.
"""

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Only backticked tokens under these top-level directories are checked.
CHECKED_ROOTS = (
    "elements",
    "just",
    "tests",
    "scripts",
    "docs",
    "files",
    "include",
    "patches",
    "plugins",
    "runbooks",
    "keys",
    ".github",
)

# Paths that are legitimately absent from the checkout: examples, retired
# files, generated or gitignored outputs, or truncated prefixes. Keep this
# list explicit; add an entry with a reason rather than loosening the regex.
ALLOWLIST = {
    # Directory-prefix mentions and examples.
    "elements/components",
    "elements/components/shiboken6.bst",
    "elements/kde-build-meta.bst",
    "elements/kde/qt6/pyside6.bst",
    "elements/kde/qt6/shiboken6.bst",
    "patches/freedesktop-sdk/0012",
    # Generated or gitignored (see docs/adr/0005-fakecap-manifest-is-generated.md).
    "files/fakecap-manifest.tsv",
    "files/fakecap/fakecap-restore.c",
    # Documented as historical / not present in this tree.
    "include/_private/aliases.yml",
    "scripts/ci-build-matrix.py",
    # A path in GNOME/gnome-build-meta, named by the proto-installer
    # provenance record (files/kde-linux-system/live/proto-installer/README.md).
    "files/gnomeos/live/proto-installer",
}

BACKTICKED = re.compile(r"`([^`\s]+)`")
PATH_TOKEN = re.compile(r"[A-Za-z0-9_./-]+")
MD_LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)\s]*)?\)")
LOG_PATH = re.compile(r"/\S*tromso-build\.log")


def _markdown_files():
    out = subprocess.run(
        ["git", "-C", str(REPO), "ls-files", "-z", "*.md"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    return [p for p in out.split("\0") if p]


def _lines(rel):
    return (REPO / rel).read_text(encoding="utf-8").splitlines()


def test_markdown_references_exist():
    """Backticked repo paths and relative links must resolve."""
    problems = []
    for rel in _markdown_files():
        base = (REPO / rel).parent
        for lineno, line in enumerate(_lines(rel), 1):
            for tok in BACKTICKED.findall(line):
                # Drop `:line` / `#anchor` suffixes and trailing punctuation.
                path = re.split(r"[:#]", tok, maxsplit=1)[0].rstrip(".,;)")
                if not PATH_TOKEN.fullmatch(path):
                    continue
                if path.split("/", 1)[0] not in CHECKED_ROOTS or "/" not in path:
                    continue
                if path in ALLOWLIST or path.rstrip("/") in ALLOWLIST:
                    continue
                if not (REPO / path).exists():
                    problems.append(f"{rel}:{lineno}: `{path}` does not exist")
            for link in MD_LINK.findall(line):
                if re.match(r"([a-z][a-z0-9+.-]*:|/)", link, re.I):
                    continue
                if not (base / link).exists():
                    problems.append(f"{rel}:{lineno}: link ({link}) does not exist")
    assert not problems, (
        "Stale Markdown references (fix the doc, or allowlist with a reason "
        "in tests/pytest/test_doc_references.py):\n" + "\n".join(problems)
    )


def test_build_log_paths_match_recipe():
    """README.md/AGENTS.md build-log paths must equal LOG= in buildstream.just."""
    recipe = (REPO / "just" / "buildstream.just").read_text(encoding="utf-8")
    logs = set(re.findall(r"^\s*LOG=(\S*tromso-build\.log)\s*$", recipe, re.M))
    assert len(logs) == 1, f"expected one LOG= build-log value, found {sorted(logs)}"
    (expected,) = logs

    problems = []
    for rel in ("README.md", "AGENTS.md"):
        for lineno, line in enumerate(_lines(rel), 1):
            for found in LOG_PATH.findall(line):
                found = found.rstrip(".,;:)`")
                if found != expected:
                    problems.append(
                        f"{rel}:{lineno}: build log path {found} != "
                        f"{expected} (LOG= in just/buildstream.just)"
                    )
    assert not problems, "\n".join(problems)

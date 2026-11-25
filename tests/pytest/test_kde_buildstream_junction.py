"""The kde-buildstream junction must stay pinned, aliased and unused.

``elements/kde-buildstream.bst`` pins the official KDE BuildStream project
(tuna-os/tromso#521, docs/UPSTREAM-ALIGNMENT.md). It is added as an *inert*
junction: nothing may depend on it until the migration step that switches the
first element group, because any reference pulls a second freedesktop-sdk
(26.08) into a 25.08 graph and changes what the image ships.

That step must update ``ALLOWED_USERS`` below in the same pull request, with
CI green and a boot proof. Until then this file keeps "added a junction" from
silently becoming "changed the published image".

Pure source inspection: no BuildStream, no network, stdlib only.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ELEMENTS = REPO / "elements"
JUNCTION = ELEMENTS / "kde-buildstream.bst"
WORKFLOW = REPO / ".github" / "workflows" / "track-bst-sources.yml"

# Elements (relative to elements/) that may reference the junction. Empty
# while the junction is inert.
ALLOWED_USERS = frozenset()

REFERENCE = re.compile(r"\bkde-buildstream\.bst\b")


def _text(path):
    return path.read_text(encoding="utf-8")


def test_junction_is_pinned_to_a_commit():
    text = _text(JUNCTION)
    assert re.search(r"^kind:\s*junction\s*$", text, re.MULTILINE)
    refs = re.findall(r"^\s*ref:\s*(\S+)\s*$", text, re.MULTILINE)
    assert len(refs) == 1, f"expected exactly one ref, found {refs}"
    assert re.fullmatch(r"[0-9a-f]{40}", refs[0]), (
        "kde-buildstream has no tags; pin a full commit id, not a branch"
    )


def test_junction_url_is_aliased_to_the_official_project():
    urls = re.findall(r"^\s*url:\s*(\S+)\s*$", _text(JUNCTION), re.MULTILINE)
    assert urls == ["kde:packaging/kde-buildstream.git"], urls


def test_no_element_uses_the_junction_yet():
    users = set()
    for path in ELEMENTS.rglob("*.bst"):
        if path == JUNCTION:
            continue
        # Comments may name the junction; only YAML content counts.
        body = "\n".join(
            line.split(" #", 1)[0]
            for line in _text(path).splitlines()
            if not line.lstrip().startswith("#")
        )
        if REFERENCE.search(body):
            users.add(path.relative_to(ELEMENTS).as_posix())
    unexpected = users - ALLOWED_USERS
    assert not unexpected, (
        "These elements use kde-buildstream.bst. That changes the published "
        "image: update ALLOWED_USERS in the same pull request, with a full "
        f"build and a boot proof (tuna-os/tromso#521): {sorted(unexpected)}"
    )


def test_project_conf_does_not_load_the_junction():
    conf = "\n".join(
        line
        for line in _text(REPO / "project.conf").splitlines()
        if not line.lstrip().startswith("#")
    )
    assert not REFERENCE.search(conf), (
        "project.conf must not include files or plugins from "
        "kde-buildstream.bst: a global change invalidates every cache key"
    )


def test_source_tracking_does_not_cover_the_junction():
    paths = re.findall(r'^\s*paths:\s*"([^"]+)"\s*$', _text(WORKFLOW), re.MULTILINE)
    assert paths, "no tracking paths found in track-bst-sources.yml"
    for entry in paths:
        for path in entry.split():
            assert path.rstrip("/") not in (
                "elements",
                "elements/kde-buildstream.bst",
            ), (
                "the junction pin moves by hand, with review; automatic "
                "tracking with automerge must not cover it"
            )

"""Guard: the local-cache recipes run a pinned, verified bst-ci script.

`just bootstrap-cache` and `just build-local` download
tuna-os/bst-ci's cas_bootstrap.py and run it as the developer's own user, so
the download must come from an immutable commit and pass a SHA-256 check
first. The recipes must also stay read-only: a developer machine never
writes to the shared CI cache.

Stdlib only.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOCAL_CACHE = (REPO / "just" / "local-cache.just").read_text()
BUILDSTREAM_JUST = (REPO / "just" / "buildstream.just").read_text()


def _const(name):
    m = re.search(rf'^export {name}\s*:=\s*"([^"]*)"', LOCAL_CACHE, re.M)
    assert m, f"{name} is not defined in just/local-cache.just"
    return m.group(1)


def test_justfile_imports_the_recipes():
    assert 'import "just/local-cache.just"' in (REPO / "Justfile").read_text()


def test_bst_ci_rev_is_a_real_full_commit_sha():
    rev = _const("bst_ci_rev")
    assert re.fullmatch(r"[0-9a-f]{40}", rev)
    assert set(rev) != {"0"}, "placeholder pin"


def test_script_digests_are_sha256():
    for name in ("cas_bootstrap_sha256", "cas_transport_sha256"):
        digest = _const(name)
        assert re.fullmatch(r"[0-9a-f]{64}", digest), name
        assert set(digest) != {"0"}, f"placeholder digest: {name}"


def test_no_mutable_ref_fetch():
    urls = re.findall(r"raw\.githubusercontent\.com/\S+", LOCAL_CACHE)
    assert urls
    for url in urls:
        assert "${bst_ci_rev}" in url, f"unpinned fetch: {url}"
        assert "/main/" not in url and "/master/" not in url


def test_scripts_are_verified_before_install_and_run_from_the_pinned_dir():
    assert "sha256sum -c --strict" in LOCAL_CACHE
    assert LOCAL_CACHE.index('verify "$TMP" ||') < LOCAL_CACHE.index('mv -f "$TMP/cas_bootstrap.py"')
    for call in re.findall(r"python3 (\S+)", LOCAL_CACHE):
        assert call in ('"${HOME}/.cache/bst-ci/${bst_ci_rev}/cas_bootstrap.py"', '"$SCRIPT"'), call
    for recipe in ("cache-list", "bootstrap-cache", "cache-status", "build-local"):
        assert re.search(rf"^{recipe}\b.*: _cas-bootstrap-fetch$", LOCAL_CACHE, re.M), recipe


def test_recipes_never_write_to_the_registry():
    for word in ("oras push", "oras login", "podman push", "skopeo copy", "GITHUB_TOKEN"):
        assert word not in LOCAL_CACHE, word
    assert "tuna-os/tromso" in _const("cache_repository")


def test_bst_recipe_honours_bst_cache_dir():
    assert 'CACHE_DIR="${BST_CACHE_DIR:-${HOME}/.cache/buildstream}"' in BUILDSTREAM_JUST
    assert '-v "${CACHE_DIR}:/root/.cache/buildstream:rw"' in BUILDSTREAM_JUST
    assert "${BST_CACHE_DIR:-${HOME}/.cache/buildstream}" in LOCAL_CACHE

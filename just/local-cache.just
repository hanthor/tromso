# ── Local builds from the CI cache ───────────────────────────────────
# CI publishes the BuildStream CAS of each build stage on GHCR
# (ghcr.io/tuna-os/tromso/cache-tromso-<stage>:latest, public). These recipes
# copy it into the local BuildStream cache, so `bst build` rebuilds only the
# elements whose cache key differs from main. They only read the registry.
#
# The script is tuna-os/bst-ci's scripts/cas_bootstrap.py, shared with
# brussels. It is fetched at a pinned commit and checked against SHA-256
# before it runs; this repository keeps no copy. To bump: pick a reviewed
# bst-ci commit and update the rev and both digests together.
export bst_ci_rev := "1f79e301af8cd6d719826f6838b4ff67c609d2eb"
export cas_bootstrap_sha256 := "7f1bc2a642562bb9198706f9e77f834810fa08c488501a03980fa72f2035ca4b"
export cas_transport_sha256 := "513f1b48640c4533e5e5bb40b403bfb2a62c9bd16b138576fa103aab2af280cf"

# GHCR repository and image name of the published cache.
export cache_repository := "tuna-os/tromso"
export cache_image := "tromso"

[private]
_cas-bootstrap-fetch:
    #!/usr/bin/env bash
    set -euo pipefail
    DIR="${HOME}/.cache/bst-ci/${bst_ci_rev}"
    BASE="https://raw.githubusercontent.com/tuna-os/bst-ci/${bst_ci_rev}/scripts"
    verify() {
        printf '%s  %s\n' \
            "${cas_bootstrap_sha256}" "$1/cas_bootstrap.py" \
            "${cas_transport_sha256}" "$1/cas_transport.py" \
            | sha256sum -c --strict --quiet - >/dev/null 2>&1
    }
    if verify "$DIR"; then
        exit 0
    fi
    echo "Downloading bst-ci cache scripts @ ${bst_ci_rev:0:12}…" >&2
    TMP="$(mktemp -d)"
    trap 'rm -rf "$TMP"' EXIT
    curl -fsSL "$BASE/cas_bootstrap.py" -o "$TMP/cas_bootstrap.py"
    curl -fsSL "$BASE/cas_transport.py" -o "$TMP/cas_transport.py"
    verify "$TMP" || { echo "bst-ci script checksum mismatch; refusing to run it." >&2; exit 1; }
    mkdir -p "$DIR"
    mv -f "$TMP/cas_bootstrap.py" "$TMP/cas_transport.py" "$DIR/"

# Show the published cache archives (size, date, digest). Default stage: core
[group('build')]
cache-list *STAGES: _cas-bootstrap-fetch
    python3 "${HOME}/.cache/bst-ci/${bst_ci_rev}/cas_bootstrap.py" list \
        "${cache_repository}" "${cache_image}" {{STAGES}}

# Read-only, anonymous, digest-verified and resumable. The default stage is
# core. Add chunk stages by name, e.g. `just bootstrap-cache core chunk0-cmake`.
# Set BST_CACHE_DIR to use a cache directory other than ~/.cache/buildstream.
# Seed the local BuildStream cache from the published CI cache
[group('build')]
bootstrap-cache *STAGES: _cas-bootstrap-fetch
    python3 "${HOME}/.cache/bst-ci/${bst_ci_rev}/cas_bootstrap.py" pull \
        "${cache_repository}" "${cache_image}" \
        "${BST_CACHE_DIR:-${HOME}/.cache/buildstream}" {{STAGES}}

# Count how many elements of a target are already in the local cache
[group('build')]
cache-status target='oci/tromso.bst': _cas-bootstrap-fetch
    #!/usr/bin/env bash
    set -euo pipefail
    BST_FLAGS="--no-interactive " just bst show --deps all --format "'%{name}||%{state}'" {{target}} \
        | python3 "${HOME}/.cache/bst-ci/${bst_ci_rev}/cas_bootstrap.py" states

# Prints the cached/to-build counts first and BuildStream's queue summary
# last. It adds no artifact server, and project.conf has no push server, so
# nothing leaves the machine.
# Build a target from the local cache and report what the cache saved
[group('build')]
build-local target='oci/tromso.bst': _cas-bootstrap-fetch
    #!/usr/bin/env bash
    set -euo pipefail
    SCRIPT="${HOME}/.cache/bst-ci/${bst_ci_rev}/cas_bootstrap.py"
    LOG="$(mktemp -t tromso-build-local.XXXXXX.log)"
    echo "==> Before the build:"
    BST_FLAGS="--no-interactive " just bst show --deps all --format "'%{name}||%{state}'" {{target}} \
        | python3 "$SCRIPT" states
    echo "==> Building {{target}} (log: $LOG)"
    START=$(date +%s)
    RC=0
    BST_FLAGS="--no-interactive ${BST_FLAGS:-}" just bst build {{target}} 2>&1 | tee "$LOG" || RC=$?
    echo "==> BuildStream summary after $(( $(date +%s) - START ))s:"
    grep -E '^\s*(Pull|Fetch|Build) Queue:' "$LOG" | tail -3 || true
    exit "$RC"

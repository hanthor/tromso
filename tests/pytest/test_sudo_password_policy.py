"""The installed image asks for a password before sudo (tuna-os/tromso#475).

freedesktop-sdk ships two sudoers elements: ``vm/config/sudo.bst`` installs
``%wheel ALL=(ALL) ALL``, and ``vm/config/sudo-nopasswd.bst`` adds
``%wheel ALL=(ALL) NOPASSWD: ALL`` for throwaway test VMs. The OCI stack once
staged both, and the last matching sudoers entry wins, so every administrator
on an installed system had root with no prompt.

The live ISO is not covered here: ``tromso/src/configure-live.sh`` writes its
own rule for ``liveuser`` when the ISO is built, outside ``elements/`` and
``files/``.

Pure source inspection: stdlib only.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ELEMENTS = REPO / "elements"
FILES = REPO / "files"

DEPENDENCY_RE = re.compile(r"^\s*-\s+(?:filename:\s*)?(\S+\.bst)\s*$")


def dependencies():
    """Yield (element, dependency) for every dependency line under elements/."""
    for element in sorted(ELEMENTS.rglob("*.bst")):
        for line in element.read_text().splitlines():
            match = DEPENDENCY_RE.match(line)
            if match:
                yield element.relative_to(REPO).as_posix(), match.group(1)


def test_wheel_sudo_rule_is_the_one_that_asks_for_a_password():
    staged = {dep: element for element, dep in dependencies()}
    assert "freedesktop-sdk.bst:vm/config/sudo.bst" in staged, (
        "no element stages vm/config/sudo.bst, so wheel has no sudo rule at all"
    )
    nopasswd = sorted(
        element for element, dep in dependencies() if dep.endswith("sudo-nopasswd.bst")
    )
    assert not nopasswd, (
        f"{nopasswd} stage freedesktop-sdk's test-VM sudoers rule, which gives "
        "every wheel member root without a password"
    )


def test_no_nopasswd_grant_in_image_sources():
    offenders = []
    for root in (ELEMENTS, FILES):
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            text = path.read_text(errors="ignore")
            for number, line in enumerate(text.splitlines(), 1):
                if "NOPASSWD" in line and not line.lstrip().startswith("#"):
                    offenders.append(f"{path.relative_to(REPO).as_posix()}:{number}")
    assert not offenders, (
        f"{offenders} grant sudo without a password in the installed image"
    )

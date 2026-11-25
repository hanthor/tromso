# The official KDE BuildStream project (invent.kde.org/packaging/kde-buildstream).
# KDE Linux builds its `testing-buildstream` edition from it.
#
# INERT ON PURPOSE: no element in this repository depends on this junction,
# so it does not change any cache key or the published image. It pins the
# upstream state that docs/UPSTREAM-ALIGNMENT.md compares against, and it is
# the "parallel junction" for trial builds that ADR 0003 asks for.
#
# A trial target does not resolve yet. `just bst show
# kde-buildstream.bst:qt/qtbase.bst` fetches this project and its nested
# freedesktop-sdk 26.08 (the patch queue applies), then stops with "Project
# 'buildstream-plugins-community' was loaded in multiple contexts": Tromsø
# pins 2.3.0, the upstream pins a branch commit. An override of both plugin
# junctions to the Tromsø ones was tried and is not enough: 2.3.0 "does not
# declare a source plugin named: 'anitya'". So tuna-os/tromso#526 must first
# move buildstream-plugins-community to a version with every source kind the
# upstream project.conf lists (anitya, cargo2, cpan, git_module, git_repo,
# go_mod_vendor, patch_queue, pypi, zip), then add the two overrides here.
#
# tests/pytest/test_kde_buildstream_junction.py keeps it inert. The first
# element that uses it must change that test in the same pull request
# (tuna-os/tromso#521, steps 10 to 12).
#
# The nested freedesktop-sdk.bst junction (release/26.08) is NOT overridden
# yet. Tromsø is on 25.08, and the upstream elements need 26.08. The override
# `freedesktop-sdk.bst: freedesktop-sdk.bst` lands with the first real use,
# after the base update (step 4).
#
# The upstream has no tags, so the ref is a plain commit id. Update it by
# hand; .github/workflows/track-bst-sources.yml does not track this file.
kind: junction

sources:
- kind: git_repo
  url: kde:packaging/kde-buildstream.git
  track: master
  ref: ee0596eed22fe46a45c357ee976022c47088f9e2

config:
  options:
    arch: '%{arch}'

# Contributing

Thank you for your interest in this project! It is part of the [TunaOS](https://tunaos.org) ecosystem.

<!-- hive-contribute-plea: donated-compute appeal, keep in sync across repos -->
## Contribute compute — no code needed

**[Donate time with your AI CLI](https://hub.tunaos.org/#contribute).**

Your machine runs one task at a time using your signed-in AI coding CLI.
The relay alternates between eligible **School** (OS) and **Reef** (apps)
hives after each task. If one hive has no work, the other can continue.

The guide covers prerequisites, verified `just` setup, credentials, provider
costs, and how to stop with Ctrl+C. Your subscription quota or API charges apply.
Never post account credentials or API keys in issues or pull requests.

## Getting Started

1. Fork the repo and clone it locally.
2. Read the [project README](README.md) and
   [CI and ISO pipeline guide](docs/ci-and-iso-pipeline.md).
3. Open an issue to discuss your change before you submit a PR.

BuildStream must run through the repository's pinned container wrapper. Do
not invoke `bst` directly on the host:

```bash
just bst show --deps all oci/tromso.bst
```

## Validation

Run the checks for your change before you open a pull request:

```bash
# Parse all Just recipes
just --summary >/dev/null
just --evaluate >/dev/null

# Unit tests (requires bats and pytest)
just test
# Or directly: bats tests/bats/*.bats && pytest tests/pytest/ -v --tb=short

# Container linting (requires built image)
just lint

# Validate the shipping BuildStream graph in the pinned container
just bst --no-interactive show --deps all oci/tromso.bst
```

Changes to shell scripts, YAML, or GitHub Actions should also run
ShellCheck, yamllint with `.yamllint.yml`, or actionlint respectively.

Two other CI checks can fail a pull request:

- The `actions-security` workflow verifies `.github/workflows/actions.lock`
  and scans the workflows with zizmor. If you change a `uses:` line in a
  workflow, update `actions.lock` in the same pull request.
- The `Prose` workflow (`ste.yml`) checks `README.md`, `CONTRIBUTING.md`,
  `SECURITY.md` and the files in `docs/` against Simplified Technical English.
  The budget in `.ste-budget` is `0`, so one new STE problem in these files
  makes the check fail. To run the same linter, you need Node.js and a clone
  of [tuna-os/.github](https://github.com/tuna-os/.github). From the root of
  this repository, run:

  ```bash
  node ../.github/.github/actions/ste-lint/ste-lint.mjs --max 0
  ```

  Change `../.github` if you cloned tuna-os/.github to a different directory.

## Pull Requests

- Keep PRs focused — one change per PR.
- Follow the existing code style and conventions.
- Update docs if your change affects usage.

## Questions?

- [TunaOS Documentation](https://tunaos.org)
- [Tromso GitHub Issues](https://github.com/tuna-os/tromso/issues)

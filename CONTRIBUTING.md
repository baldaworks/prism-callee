# Contributing to Prism Callee

## Ownership and integrity

`plugins/prism-callee/` owns the coding-agent wrapper and its flat mirror.
`pack/callee/` owns the extracted workflow agents, including `prism/lifecycle`,
`prism/story`, and `prism/epic`. The
[ownership manifest](docs/lifecycle-ownership.json) records the checked sources
and digests. See [Callee architecture](docs/architecture-callee-lifecycle.md)
for the runtime contracts.

Prism Callee and the [primary Prism repository](https://github.com/baldaworks/prism)
each have their own marketplace, integrity inventory, and CI. They install and
validate independently. Keep mandatory cross-links pointed at the exact
repository destinations.

## Validation

Run all six native checks from the repository root before completing a change:

```sh
./scripts/validate-plugin-packaging.sh
./scripts/validate-lifecycle-ownership.sh
./scripts/validate-documentation.sh
./scripts/test-lifecycle-drift-detection.sh
./scripts/test-documentation-drift-detection.sh
./scripts/test-callee-lifecycle-forward-contracts.sh
```

Packaging and ownership checks protect manifests, mirrors, and source digests.
Documentation checks cover required content, links, and diagrams; mutation
fixtures prove that selected regressions fail validation. Forward fixtures use
a temporary Beads database and check lifecycle invariants. These checks do not
prove every model execution follows the instructions or validate every user's
live Story or Epic. Review the actual change and its relevant behavior as well.

Provider-backed smoke tests are optional maintainer checks documented in the
[Human smoke-test guide](docs/callee-lifecycle-smoke-test.md).

When editing user documentation, keep the README focused on installation,
catalog import, and the supported full-workflow entrypoints. Keep ownership,
validation, and publication policy here.

## Commit and publication policy

Verified repository tasks are committed after their required checks pass.
Pushing and publishing require explicit authorization.

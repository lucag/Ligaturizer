# The Ligature source is built from the pinned Fira Code submodule

The Fira Code OTFs we transplant from are built locally from the `fonts/fira` submodule using Fira's own build, rather than downloaded from a release or committed to this repo. The submodule commit is therefore the single pin for which Fira Code the Output fonts and the tests are measured against.

## Considered Options

- **Download a pinned release zip:** lighter, but ties us to Fira's release cadence (the current submodule is 33 commits past the last tag).
- **Commit built OTFs:** simple, but duplicates binaries and can drift from the submodule.

## Consequences

Anyone building or testing needs Fira's build toolchain (or its Docker image); CI must build Fira too, ideally cached by submodule commit.

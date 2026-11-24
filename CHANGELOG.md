# Changelog

## [Unreleased]

### CI

- Pushes and pull requests run the Org conformance workflow (github-workflows v6.5.0). Pull requests targeting `main` require the `org-conformance / org-conformance` check.
- Add the canonical workflow-level `concurrency` to `ci.yml`: a superseded pull-request run is cancelled.

### Removed

- Drop the tracked `.agent-plans/.gitignore`: plans now live in the common git directory.

### Fixed

- Keep agent plans and scratch data out of Git while tracking the directory ignore rules.

## [0.1.0] - 2026-11-14

### Fixed

- Run public repository validation on GitHub-hosted Ubuntu runners so checks can start without access to private organization runners.

### Added

- Extract geographic evidence contracts and processing from geohistory.

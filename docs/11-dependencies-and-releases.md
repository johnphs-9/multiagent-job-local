# Dependencies and Releases

This project is a personal, single-user academic showcase. Releases are reproducible
source snapshots, not a hosted service or a promise of multi-user support.

## Dependency update process

1. Review Python and npm updates monthly, and immediately for security advisories.
2. Update the Python dependency lockfile (when introduced) and `frontend/package-lock.json`
   in separate commits where practical.
3. Run `make test`, `make lint`, and `npm run build --prefix frontend`.
4. Run the Preview smoke test with the pinned local Ollama model.
5. Review privacy, model output, and API compatibility changes before merging.
6. Record notable changes in [CHANGELOG.md](../CHANGELOG.md).

## Release workflow

1. Update `__version__` in `src/job_interviewer/__init__.py` using semantic versioning.
2. Update `CHANGELOG.md` with the release date and user-visible changes.
3. Update `__build_tag__` or `APP_BUILD_TAG` for the demonstrable build.
4. Run all quality checks and verify the README setup from a clean checkout.
5. Create a signed or annotated Git tag such as `v0.3.0` and publish the GitHub release.

The release is considered local-only unless the threat model, authentication, persistence,
and deployment documentation are explicitly expanded.

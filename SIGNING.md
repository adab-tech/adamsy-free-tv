# Code signing (Windows installer)

The Windows installer built by `.github/workflows/build-windows-installer.yml`
is currently **unsigned**. Windows SmartScreen flags unsigned, low-reputation
executables with a "Windows protected your PC" warning - this is expected
and documented in `TESTING.md`. Signing it with a real code-signing
certificate is what gets past that.

This project uses **[SignPath.io](https://signpath.io)'s free code-signing
program for open source projects**, since the repository is public and MIT
licensed (see `LICENSE`). SignPath issues and holds the actual certificate
in their cloud HSM - nothing signing-related is stored in this repo.

## What's already done

- The repo is public with an OSI-approved license (MIT), which SignPath's
  program requires.
- `build-windows-installer.yml` already has a signing step wired in
  (`signpath/github-action-submit-signing-request`). It's conditional on
  `vars.SIGNPATH_PROJECT_SLUG` being set - until that's configured, the
  workflow silently skips signing and uploads the unsigned installer, exactly
  like it does today. No further code changes are needed once setup below is
  complete.

## What still needs a human (project owner)

SignPath's onboarding is tied to your own identity/GitHub account, so this
part can't be done by an AI session - only the project owner can apply:

1. Go to <https://signpath.io/apply-for-free-code-signing> and apply for the
   open source program, linking `adab-tech/adamsy-free-tv`.
2. Once approved, in the SignPath dashboard create:
   - An **Organization** (if you don't have one yet).
   - A **Project** for this repo.
   - A **Signing Policy** (SignPath's free tier typically provides a
     `test-signing` policy immediately and a `release-signing` policy after
     a short review - use whichever is approved for public releases).
   - An **Artifact Configuration** describing the file to sign (a single
     Windows executable/installer - no special configuration needed beyond
     the default authenticode template).
   - An **API Token** scoped to submitting signing requests for this project.
3. In the GitHub repo, add:
   - **Settings → Secrets and variables → Actions → Secrets**:
     `SIGNPATH_API_TOKEN`
   - **Settings → Secrets and variables → Actions → Variables**:
     `SIGNPATH_ORGANIZATION_ID`, `SIGNPATH_PROJECT_SLUG`,
     `SIGNPATH_SIGNING_POLICY_SLUG`, `SIGNPATH_ARTIFACT_CONFIGURATION_SLUG`
     (values come from the SignPath dashboard - these aren't secret, just
     identifiers, so they go in Variables rather than Secrets).
4. Re-run `build-windows-installer.yml` (workflow_dispatch, or it'll run
   automatically on the next release) - the installer will now be signed
   before it's attached to the release.

## A note on SmartScreen specifically

Signing removes the "unknown publisher" problem, but SmartScreen's full
warning also depends on **reputation** built from real download volume over
time. Expect a milder prompt (not a full block) immediately after signing
starts, with warnings disappearing entirely as more people download and run
signed releases. This is normal and not something signing itself controls.

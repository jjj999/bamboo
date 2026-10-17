# AGENTS.md

Project-specific guidance for AI coding agents will be defined separately.

## Git operations

- Follow the Issue-based workflow and commit message rules in
  `CONTRIBUTING.md`; it is the source of truth.
- Write commit messages in English.
- Codex, Claude Code, and other coding agents must not create commits unless
  explicitly instructed to do so.
- Run commit, push, and release operations only when explicitly requested.

## Issue-based development

- For implementation, bug-fix, and refactoring requests, use `gh` or the
  GitHub API to search open and closed Issues before changing code. Reuse a
  matching Issue instead of creating a duplicate.
- If no matching Issue exists, create one automatically in English before
  implementation. Include the Background, Scope, Implementation Notes, and
  Acceptance Criteria sections defined in `CONTRIBUTING.md`.
- Do not create Issues for consultation, explanation, or read-only
  investigation requests.
- Check available repository labels before applying the most relevant one.
  Do not invent or duplicate labels.
- Create and update Issues through `gh` or the GitHub API, and report when a
  requested label is unavailable instead of creating repository labels.
- If GitHub access or Issue creation fails, report the failure and do not use
  a fabricated Issue number.
- Create the Issue-numbered branch when implementation begins, then modify
  code and run relevant tests without requesting separate authorization.
- Search Issues, check duplicates, create implementation Issues, add labels,
  and create branches automatically. Creating commits, pushing, creating or
  merging pull requests, and releasing require explicit authorization.
- Relate Issues in PR bodies with `Refs #<number>`. Add
  `Issue-Closure: #<number>` only for Issues completed by a PR targeting
  `develop`; the GitHub Actions workflow closes them after merge.
- Do not close Issues directly in the normal workflow. Let GitHub Actions
  close marked Issues after a successful merge into `develop`.

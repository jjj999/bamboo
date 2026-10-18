# Contribution Guide

This is the contribution guide for the bamboo project. All developers must read the guide and get started to develop.

## Development environment

Bamboo officially supports Python 3.11 through 3.15. Python 3.14 is the
standard development version. The project intentionally has no Python upper
bound, but versions newer than 3.15 are not part of the tested support policy.
Poetry 2.5.1 manages the development environment and creates `.venv` in the
repository.

### Dev Container (recommended)

1. Install Docker and the VS Code Dev Containers extension on the host.
2. Open this repository in VS Code and run **Dev Containers: Reopen in
   Container**.
3. Wait for `postCreateCommand` to install the Poetry environment and Codex
   CLI. The command is safe to run again as
   `bash .devcontainer/post-create.sh`.

The container uses Debian Bookworm, Python 3.14, Node.js 24 LTS, Poetry 2.5.1,
GitHub CLI, and a non-root `vscode` user. It does not use privileged mode or
mount the Docker socket. GitHub CLI is installed through the official
`ghcr.io/devcontainers/features/github-cli` Dev Container Feature.

Codex CLI is installed from the official `@openai/codex` npm package. Run
`codex` and follow the interactive sign-in flow. Claude Code is installed by
Anthropic's official Dev Container Feature; run `claude` and follow its
interactive sign-in flow. Login is deliberately left to each developer. Do
not put API keys or either tool's authentication files in this repository.
Credentials are not mounted from the host, so rebuilding the container may
require signing in again.

Authenticate GitHub CLI interactively after creating the container:

```console
gh auth login --web --git-protocol https
gh auth status
```

Choose `github.com` and sign in with an account that can read and write Issues
and pull requests in this repository. Automation that also pushes branches
needs repository Contents write access. For a fine-grained token, grant
Contents, Issues, and Pull requests access only as required; a classic token
needs the equivalent `repo` access. Run `gh auth setup-git` if Git should use
the GitHub CLI credential helper. For non-interactive environments, pass a
suitably scoped token through the `GH_TOKEN` environment variable instead of
writing it to the repository. Never commit tokens, GitHub CLI configuration,
or authentication files. Container-local credentials may need to be restored
after rebuilding the container.

The corresponding `openai.chatgpt` and `anthropic.claude-code` VS Code
extensions are installed inside the container automatically.

### Local setup

Outside the Dev Container, install Python 3.11 or newer and Poetry 2.5.1, then
run:

```console
make install
```

### Common commands

```console
make test-unit          # tests without external servers
make test-integration   # WSGI/ASGI and network tests
make test-slow          # explicit 1 GB transfer tests
make test-all           # unit + integration, excluding slow tests
make lint               # Ruff lint
make format-check       # check Ruff formatting without changes
make format             # apply Ruff formatting intentionally
make typecheck          # Pyright basic checking
make build              # build wheel and source distribution
make check              # lint + typecheck + normal tests
```

Plain `poetry run pytest` also excludes tests marked `slow`. The 1 GB test
resource is generated in pytest's temporary directory only for an explicitly
selected slow test and is removed afterward.

Generate a terminal coverage report with:

```console
poetry run pytest --cov=bamboo --cov-report=term-missing
```

VS Code uses `.venv/bin/python`, pytest, debugpy, and Ruff as the formatter.
Format-on-save and Ruff's save-time fixes are initially disabled to avoid an
unrelated repository-wide rewrite. Use the supplied launch configurations to
debug the current Python file or the current pytest file.

### pre-commit

Install the Git hook once after `make install`:

```console
poetry run pre-commit install
```

Run all configured Ruff, whitespace, YAML, and TOML checks manually with:

```console
poetry run pre-commit run --all-files
```

## Git development flow

We employ [the branching model](https://nvie.com/posts/a-successful-git-branching-model/) as the git development flow for the project.

### The main branches

In the flow, we have two important branches:

- `main` branch
- `develop` branch

These branches has the common feature that they are not to vanish. On the other hand, their roles are not common; the `main` branch heads the newest and stable version of the package and the `develop` branch heads the next release of the package.

### Version tags

As explained above, the `main` and `develop` branches have their version tags to identify the package content. Note that there is a tagging rules for the branches.

First, the tags consist of three numbers joined by dot, e.g. `0.1.2`. We often say the first number as **major number**, the second **minor number** and the last **patch number**. Second, the `develop` branch must have the tag whose minor number is the next number of the one of the `main` branch and patch number is zero. For example, if the `main` branch heads version `1.3.6`, then the `develop` branch heads version `1.4.0`.

Althogh Some developers might think the second rule is awkward, the reseason is that the minor number increases when new features of the package are released, and the patch number increase when some reported bugs of the stable version at that time are fixed. As you can see later, tasks of feature implamentation and bug fixing are conducted in different types of branches, and the branches in which feature implementations are conducted are to be merged into the `develop` branch. Therefore, the `develop` branch always has new features of the package but the features are not fixed by bug reports. Thus, the `develop` branch has the tag whose minor number is the next of the `main` and patch number is zero.

### Supporting branches

We also other three types of branches in development:

- `feature` branches
- `release` branches
- `hotfix` branches

In the `feature` branches, developers implements new features suggested in issues. The feature branches always are derived from the `develop` branch and merged into the `develop` branch through pull requests and deleted eventually. These branches can be identified by issue numbers and names of the branches should has the rule of `feature-issXXX` (`XXX` is the issue number).

The `release` branches exist for placing the pre-stages of new releases. In the branches, developers do some tests mainly and fix bugs if they are caught. The branches are to be merged if they can be released and deleted. These branches can be identified by the next release number and should be named as `release-X.X` (`X.X` is a pair of a major number and a minor number).

The `hotfix` branches are created when the project receives bug reports. The branches always are derived from the `main` branch and merged into both of the `main` and `develop` branches because the reported bugs will be in the package which the `main` branch heads and also `develop` branch heads. The branches are deleted if the merges finish. Because these branches can be identified by issue numbers, the branches should be named as `hotfix-issXXX` (`XXX` is the issue number).

### `gh-pages` branch

The `gh-pages` branch is only for the site of the package hosted by the Github Pages. Developers don't have to work on the branch because the branch is changed automatically.

## New Issues

Development starts from a GitHub Issue. Before beginning implementation:

1. Search open and closed Issues for the same task.
2. Reuse an Issue when its scope matches the task.
3. Create an Issue only when no matching Issue exists.
4. Write the Issue title and body in English and apply an appropriate existing
   label.

Use GitHub CLI to search before creating an Issue:

```console
gh issue list --state all --search "route matching"
gh issue view <issue-number>
```

Create Issues from a prepared Markdown body so that shell quoting does not
alter their content:

```console
gh issue create --title "Correct overlapping route detection" \
  --body-file /path/to/issue-body.md --label bug
```

Update an existing Issue from a prepared body in the same way:

```console
gh issue edit <issue-number> --body-file /path/to/issue-body.md
```

Use `--add-label` only after confirming that the label exists. Issue creation
and updates must use GitHub CLI or the GitHub API.

Use this body structure, adapting it to the task:

```markdown
## Background

Why is this change necessary?

## Scope

What should be changed?

## Implementation Notes

Relevant modules, constraints, and technical considerations.

## Acceptance Criteria

- [ ] Required behavior is implemented.
- [ ] Relevant tests are added or updated.
- [ ] Existing tests pass.
- [ ] Public API compatibility is maintained where applicable.
```

The repository provides these Issue templates:

- Bug Reports --> [Click](https://github.com/jjj999/bamboo/issues/new?template=bug_report.md)
- Suggestion for new features --> [Click](https://github.com/jjj999/bamboo/issues/new?template=feature_request.md)
- Maintenance --> [Click](https://github.com/jjj999/bamboo/issues/new?template=maintenance.md)

Use labels such as `bug`, `enhancement`, `refactor`, `testing`, `tooling`, and
`documentation` when they exist and apply. Check the repository's current
labels before adding one; do not create duplicates.

## New Pull Requests

Developers should pull request if they want to merge their branch into the
`main` or `develop` branches. Titles and descriptions should be written in
English.

### Issue-based development workflow

1. Search for and reuse a matching Issue, or create a new one.
2. Create a branch containing the Issue number. Follow the existing
   `feature-issXXX` or `hotfix-issXXX` naming and base-branch rules above.
3. Implement the change and add or update relevant tests.
4. Include the Issue number in each related Conventional Commit subject.
5. Open a PR, reference the Issue, and identify any Issue completed by the PR.
6. Complete review and CI, then merge the PR into `develop`.
7. Treat the Issue as complete when the PR is merged into `develop`; the
   close-Issues workflow closes explicitly marked Issues automatically.

Release branches retain the existing `release-X.X` naming rule. They do not
require an Issue number unless the release work itself tracks a specific
Issue.

After pushing the branch, create the PR with an English title and a prepared
body based on the repository template:

```console
gh pr create --base develop --title "Correct overlapping route detection" \
  --body-file /path/to/pull-request-body.md
```

### Relating and completing Issues

Use `Refs` in the PR body for every related Issue:

```text
Refs #25
```

For an Issue that this PR completes, add a separate marker:

```text
Issue-Closure: #25
```

Add one marker per Issue when a PR completes multiple Issues. Omit the marker
from partial or intermediate PRs and from Issues that are related but not
completed. The marker is project metadata read by GitHub Actions; it is not a
GitHub closing keyword.

After a PR is merged into `develop`, the resulting push starts
`.github/workflows/close-issues-on-develop.yml`. The workflow compares the
push's before and after commits, uses the GitHub API to find pull requests
associated with every introduced commit, and accepts only pull requests whose
merge commit is in that push and whose base is this repository's `develop`
branch. It then extracts valid markers, verifies that each number belongs to an
open Issue in this repository rather than a pull request, and closes it as
completed.

The workflow uses `push` because a `pull_request_target` workflow is loaded
from the default branch, while development automation is maintained on
`develop`. A normal direct push, force push, PR closed without merging, merge
into another branch, historical unrelated PR, or PR containing only `Refs`
does not close any Issue.

The workflow uses the repository `GITHUB_TOKEN`; its permissions are limited
to `contents: read`, `pull-requests: read`, and `issues: write`, so it does
not require a personal access token. The repository's Actions policy must allow
the Issue write permission.

To confirm a closure, open the repository's **Actions** tab, select **Close
Issues on Develop**, and inspect the run for the merge commit. The log records
the pushed commit range, matched pull request, skipped markers or Issues, and
each Issue closed as completed. If the workflow fails, first compare the run's
`before` and `after` SHAs with the merge, then inspect API error messages,
the pull request's `merged_at`, base branch, base repository, and
`merge_commit_sha`. Also confirm the exact `Issue-Closure: #<number>` lines,
the target Issue state, and the workflow's token permissions. A missing run
usually means the updated workflow was not yet present on `develop` for that
push or the repository Actions policy prevented the event.

## Commits

Commit messages must be written in English and follow
[Conventional Commits](https://www.conventionalcommits.org/). This section is
the source of truth for the project's commit message rules.

### Format

Use the following subject format:

```text
<type>(<scope>): <description> (#<issue>)
```

The scope and issue reference are optional. Include the issue reference when
the commit corresponds to an existing GitHub Issue. It may be omitted for a
minor change that has no issue.

### Types

| Type | Purpose |
|---|---|
| `feat` | New features |
| `fix` | Bug fixes |
| `refactor` | Internal changes without behavioral changes |
| `test` | Adding or modifying tests |
| `docs` | Documentation changes |
| `build` | Build system and dependency changes |
| `ci` | CI/CD configuration changes |
| `perf` | Performance improvements |
| `chore` | Other maintenance tasks |

These are the standard types. Additional types may be introduced when a clear
project need arises.

### Scope

Use an optional scope to identify the module or component affected by the
change. Examples include `app`, `asgi`, `endpoint`, `router`, `request`, `api`,
and `devcontainer`. Omit the scope when no single, useful scope applies; do not
force one.

### Subject

The subject must:

1. Be written in English.
2. Use the imperative mood.
3. Start the description with a lowercase letter.
4. Not end with a period.
5. Be no more than 72 characters whenever practical.
6. State clearly what the commit changes.
7. Avoid vague descriptions such as `update files` or `fix bug`.

Examples:

```text
fix(request): correct async HTTP argument forwarding (#12)
refactor(endpoint): simplify response handling (#13)
test(asgi): add WebSocket protocol tests (#14)
build(devcontainer): update Python environment (#15)
docs: improve installation instructions (#16)
```

### Commit body

A simple change may use only the subject. Add a body after a blank line when
the background, reason, or a technical decision needs to be recorded. Explain
what changed and why, without repeating implementation details that are clear
from the code. Wrap body lines at 72 characters whenever practical.

```text
fix(asgi): handle disconnected clients (#24)

Prevent further body reads after receiving an ASGI
disconnect event.

This avoids waiting for additional messages after the
client has already closed the connection.
```

### GitHub Issues and pull requests

When a corresponding Issue exists, add its number to the commit subject, for
example:

```text
fix(router): correct overlapping route detection (#25)
```

This reference records the relationship but does not request that the Issue
be closed. Do not use `Closes`, `Fixes`, `Resolves`, or other GitHub automatic
closing keywords in commit messages.

```text
Refs #25
```

Use `Refs` when the PR relates to an Issue without completing it. When a PR
into `develop` completes the Issue, add the project closure marker as a
separate line:

```text
Issue-Closure: #25
```

The dedicated GitHub Actions workflow, rather than GitHub's default-branch
closing behavior, processes this marker after a successful merge into
`develop`. This keeps Issue completion aligned with the project's Git Flow and
prevents a later merge into `main` from closing unrelated Issues.

### Breaking changes

Mark a breaking change using `!` before the colon or a `BREAKING CHANGE:`
footer, as defined by Conventional Commits. The footer must explain the impact
and any required migration.

```text
feat(api)!: remove legacy request interface (#30)

BREAKING CHANGE: use the request context API instead of the legacy
interface.
```

### Commit scope and granularity

Each commit should contain one logical change and be understandable on its
own. Separate unrelated bug fixes, refactoring, development environment
changes, and documentation changes whenever possible. Changes required for
the same purpose, such as a bug fix and its regression test, may remain in one
commit.

### Commit template

This repository provides [`.gitmessage`](.gitmessage) as a concise reminder of
these rules. Configure Git to use it from the repository root:

```console
git config commit.template .gitmessage
```

Then open the template by running:

```console
git commit
```

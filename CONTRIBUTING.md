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
and a non-root `vscode` user. It does not use privileged mode or mount the
Docker socket.

Codex CLI is installed from the official `@openai/codex` npm package. Run
`codex` and follow the interactive sign-in flow. Claude Code is installed by
Anthropic's official Dev Container Feature; run `claude` and follow its
interactive sign-in flow. Login is deliberately left to each developer. Do
not put API keys or either tool's authentication files in this repository.
Credentials are not mounted from the host, so rebuilding the container may
require signing in again.

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

If you have some issues, you can publish them using the templates:

- Bug Reports --> [Click](https://github.com/jjj999/bamboo/issues/new?template=bug_report.md)
- Suggestion for new features --> [Click](https://github.com/jjj999/bamboo/issues/new?template=feature_request.md)

## New Pull Requests

Developers should pull request if they want to merge their branch into the `main` or `develop` branches.

## Commits

The project has the commit template, [.gitmessage file](https://github.com/jjj999/bamboo/blob/develop/.gitmessage) . The template is for unifying the commit message style such that all developers can read the message easily. Developers should do the commond in order to set the template to git:

```
git config commit.template .gitmessage
```

After the command, developers can commit with the command:

```
git commit
```

# Contribution Guide

This is the contribution guide for the bamboo project. All developers must read the guide and get started to develop.

## Git development flow

We employ [the branching model](https://nvie.com/posts/a-successful-git-branching-model/) as the git development flow for the project.

### The main branches

In the flow, we have two important branches:

- `master` branch
- `develop` branch

These branches has the common feature that they are not to vanish. On the other hand, their roles are not common; the `master` branch heads the newest and stable version of the package and the `develop` branch heads the next release of the package.

### Version tags

As explained above, the `master` and `develop` branches have their version tags to identify the package content. Note that there is a tagging rules for the branches.

First, the tags consist of three numbers joined by dot, e.g. `0.1.2`. We often say the first number as **major number**, the second **minor number** and the last **patch number**. Second, the `develop` branch must have the tag whose minor number is the next number of the one of the `master` branch and patch number is zero. For example, if the `master` branch heads version `1.3.6`, then the `develop` branch heads version `1.4.0`.

Althogh Some developers might think the second rule is awkward, the reseason is that the minor number increases when new features of the package are released, and the patch number increase when some reported bugs of the stable version at that time are fixed. As you can see later, tasks of feature implamentation and bug fixing are conducted in different types of branches, and the branches in which feature implementations are conducted are to be merged into the `develop` branch. Therefore, the `develop` branch always has new features of the package but the features are not fixed by bug reports. Thus, the `develop` branch has the tag whose minor number is the next of the `master` and patch number is zero.

### Supporting branches

We also other three types of branches in development:

- `feature` branches
- `release` branches
- `hotfix` branches

In the `feature` branches, developers implements new features suggested in issues. The feature branches always are derived from the `develop` branch and merged into the `develop` branch through pull requests and deleted eventually. These branches can be identified by issue numbers and names of the branches should has the rule of `feature-issXXX` (`XXX` is the issue number).

The `release` branches exist for placing the pre-stages of new releases. In the branches, developers do some tests mainly and fix bugs if they are caught. The branches are to be merged if they can be released and deleted. These branches can be identified by the next release number and should be named as `release-X.X` (`X.X` is a pair of a major number and a minor number).

The `hotfix` branches are created when the project receives bug reports. The branches always are derived from the `master` branch and merged into both of the `master` and `develop` branches because the reported bugs will be in the package which the `master` branch heads and also `develop` branch heads. The branches are deleted if the merges finish. Because these branches can be identified by issue numbers, the branches should be named as `hotfix-issXXX` (`XXX` is the issue number).

### `gh-pages` branch

The `gh-pages` branch is only for the site of the package hosted by the Github Pages. Developers don't have to work on the branch because the branch is changed automatically.

## New Issues

If you have some issues, you can publish them using the templates:

- Bug Reports --> [Click](https://github.com/jjj999/bamboo/issues/new?template=bug_report.md)
- Suggestion for new features --> [Click](https://github.com/jjj999/bamboo/issues/new?template=feature_request.md)

## New Pull Requests

Developers should pull request if they want to merge their branch into the `master` or `develop` branches.

## Commits

The project has the commit template, [.gitmessage file](https://github.com/jjj999/bamboo/blob/develop/.gitmessage) . The template is for unifying the commit message style such that all developers can read the message easily. Developers should do the commond in order to set the template to git:

```
git config commit.template .gitmessage
```

After the command, developers can commit with the command:

```
git commit
```

## Initilizing development environments

First, developers should has Python 3.7 for the development and install `Pipenv`:

```
pip install --upgrade pip pipenv
```

Next, developers should run the command:

```
pipenv run init
```

That's it! Welcome the bamboo project and we all appreciate your joining!

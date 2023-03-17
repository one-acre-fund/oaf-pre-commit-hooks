# Pre-commit Hook for Git and GitHook Convention
The repository for pre-commit hooks to check Git and GitFlow conventions and best practices

## Installation
1. Install pre-commit from https://pre-commit.com/#install

2. Create or update a `.pre-commit-config.yaml` file at the root of repository with the following content:

```
repos:
  - repo: https://github.com/one-acre-fund/oaf-pre-commit-hooks
    rev: v2.0.0
    hooks:
      - id: oaf-pre-commit-hook-git-branch
      - id: oaf-pre-commit-hook-git-commit
```
3. Auto-update the config to the latest repos' versions by executing `pre-commit autoupdate`

4. Install with `pre-commit install`

## Expected Errors
1. `Git` CLI tool not installed or badly configued
2. `GitFlow` convention for naming branches:
## Report Issues

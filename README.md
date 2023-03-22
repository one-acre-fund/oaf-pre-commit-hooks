# Pre-commit Hook for Technical Standards
The repository for pre-commit hooks to check Git and GitFlow conventions and other best practices

## Installation
1. Install pre-commit from https://pre-commit.com/#install

2. Create or update a `.pre-commit-config.yaml` file at the root of repository with the following content:

```
repos:
  - repo: https://github.com/one-acre-fund/oaf-pre-commit-hooks
    rev: v1.0.0
    hooks:
      - id: oaf-tech-pre-commit-hook
```
3. Auto-update the config to the latest repos' versions by executing `pre-commit autoupdate`

4. Install with `pre-commit install`

## Expected Behaviors
1. **`Git` branching model**: to make sure branch naming convention is followed
2. **`Git` log**:  to show commit messages that do not follow conventional semantics on current branch
3. **`Pre-commit` hooks**: to check whether required pre-commit hooks are installed
4. **`Gitlint`**: to validate current commit message upon [prepare-commit-msg,commit] according to `.gitlint` config directives
## Report Issues
1. Use Slack technical channels (#dev-team-leads)
2.

#!/usr/bin/env python3
"""Helper script to be used as a pre-commit hook."""
import argparse
import os
import re
import ssl
import subprocess
import sys
import warnings
import json
from typing import Sequence
from urllib.request import urlopen


def load_config() -> dict:
    CONFIG_URL = "https://raw.githubusercontent.com/one-acre-fund/oaf-pre-commit-hooks/main/config.json"
    pre_commit_home = os.getenv("PRE_COMMIT_HOME")
    cache_dir = ""
    if pre_commit_home is None or os.path.exists(pre_commit_home) == False:
        pre_commit_home = (
            "" if os.getenv("XDG_CACHE_HOME") is None else os.getenv("XDG_CACHE_HOME")
        )
        cache_dir = pre_commit_home + "/pre-commit"
        if os.path.exists(cache_dir) == False:
            user_home = os.path.expanduser("~")
            cache_dir = user_home + "/.cache/pre-commit"
            if os.path.exists(cache_dir) == False:
                os.makedirs(cache_dir)

    config_file_path = cache_dir + "/oaf_pre-commit_config.json"
    config = {}

    if os.path.exists(config_file_path) == False:
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
            with urlopen(CONFIG_URL) as f:
                config = json.load(f)
                print(" from %s %o", CONFIG_URL, config)
                if len(config) > 1:
                    with open(config_file_path, "w") as fp:
                        json.dump(config, fp)
        except Exception as e:
            warnings.warn(e)

    if len(config) < 1:
        config = {
            "OAF_GIT_BRANCH_NAME_REGEX": "^((release\/[0-9]+\.[0-9]+\.[0-9])|((feature|feat|cleanup|bugfix|hotfix|fix|devops)\/[A-Z]+-[0-9]+(-[A-z0-9]+)+)|(umuganda|chore)\/[a-zA-Z0-9+\-]+)$",
            "OAF_GIT_BRANCH_NAME_EXCEPTION": ["develop", "main", "master"],
            "OAF_GIT_COMMIT_TYPES": [
                "feat",
                "fix",
                "style",
                "refactor",
                "docs",
                "perf",
                "test",
                "chore",
                "build",
            ],
        }
    return config


def is_hook_installed(hook) -> bool:
    """Determine if the pre-commit hook is installed and enabled."""
    exit_code = os.WEXITSTATUS(os.system("git config --bool " + hook))
    out = subprocess.getoutput("git config --bool " + hook)
    return exit_code == 0 and out == "false"


def get_current_branch_name() -> str:
    """Determine the active Git branch name."""
    return subprocess.getoutput("git rev-parse --abbrev-ref HEAD")


def get_git_branch_name_regex() -> str:
    """Read Git and GitFlow naming Regex"""
    config = load_config()
    return config["OAF_GIT_BRANCH_NAME_REGEX"]


def get_git_branch_name_exceptions() -> list:
    """Determine Git branches that are exempt from naming convention"""
    config = load_config()
    return config["OAF_GIT_BRANCH_NAME_EXCEPTION"]


def get_git_conventional_commit_types() -> list:
    """Determine Git conventional commit types"""
    config = load_config()
    return config["OAF_GIT_COMMIT_TYPES"]


def validate_git_commit(commit, force_exit=True) -> int:
    """Parse and verify git commit format"""
    commit_title = commit["title"].split(":")
    if len(commit_title) == 1:
        warnings.warn(
            "Commit %s has invalid message `%s` " % (commit["hash"], commit["title"])
        )
        if force_exit:
            return 1

    commit_ok = False
    oaf_commit_types = get_git_conventional_commit_types()
    commit_type = commit_title[0].split("(")[0]
    try:
        commit_ok = oaf_commit_types.index(commit_type) >= 0
    except ValueError:
        warnings.warn(
            "Commit %s '%s' has wrong type `%s`"
            % (commit["hash"], commit["title"], commit_type)
        )
        if force_exit:
            return 1

    return 0 if commit_ok else 1


def get_commits() -> list:
    """Get commit history on current branch"""
    lines = (
        subprocess.check_output(["git", "log"], stderr=subprocess.STDOUT)
        .decode("utf-8")
        .split("\n")
    )
    commits = []
    current_commit = {}

    def save_current_commit():
        title = current_commit["message"][0]
        message = current_commit["message"][1:]
        if message and message[0] == "":
            del message[0]
        current_commit["title"] = title.lstrip()
        current_commit["message"] = "\n".join(message)
        commits.append(current_commit)

    for line in lines:
        if not line.startswith(" "):
            if line.startswith("commit "):
                if current_commit:
                    save_current_commit()
                    current_commit = {}
                current_commit["hash"] = line.split("commit ")[1]
            else:
                try:
                    key, value = line.split(":", 1)
                    current_commit[key.lower()] = value.strip()
                except ValueError:
                    pass
        else:
            current_commit.setdefault("message", []).append(
                re.compile("^`{4}`").sub("", line)
            )
    if current_commit:
        save_current_commit()
    return commits


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="", help="check README.md")
    parser.add_argument("--forced", default=True, help="check README.md")

    args = parser.parse_args(argv)
    if len(sys.argv) == 1:
        print("How to pass args when calling the script:")
        parser.print_help()

    if (
        args.forced == False
        and is_hook_installed("hooks.oaf-pre-commit-hook-git-branch") == False
    ):
        warnings.warn(
            "Hook is not installed or disabled:(enable with 'git config hooks.oaf-pre-commit-hook-git-branch true')"
        )
        return 1

    # validate branch naming
    branch = get_current_branch_name()
    branch_ok = False
    oaf_lts_branches = get_git_branch_name_exceptions()
    try:
        branch_ok = oaf_lts_branches.index(branch) >= 0
    except ValueError:
        pass
    if branch_ok == False:
        oaf_regex = get_git_branch_name_regex()
        branch_ok = re.search(oaf_regex, branch)

    if branch_ok == False:
        warnings.warn(
            "branch %s name should follow {prefix/JIRA#-descr}:"
            "prefix=%s" % (branch, ",".join(oaf_lts_branches))
        )
        return 1

    # check commit history on this branch
    commits = get_commits()
    for commit in commits:
        exit_code = validate_git_commit(commit, False)
        if exit_code != 0:
            return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

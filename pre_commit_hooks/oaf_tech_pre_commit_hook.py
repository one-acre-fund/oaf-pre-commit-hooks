#!/usr/bin/env python3
"""Helper script to be used as a pre-commit hook."""
import argparse
import json
import os
import re
import ssl
import subprocess
import sys
from typing import Sequence
from urllib.request import urlopen

TERMINAL_COLOR_ERROR = "\033[1;31;40m"
TERMINAL_COLOR_WARNING = "\033[1;33;40m"
TERMINAL_COLOR_NORMAL = "\033[0;37;40m"
TERMINAL_COLOR_PASS = "\033[1;32;40m"
oaf_config = {"cache": [], "live": []}


def load_config() -> int:
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

    try:
        config_url = "https://raw.githubusercontent.com/one-acre-fund/oaf-pre-commit-hooks/main/config.json"
        ssl._create_default_https_context = ssl._create_unverified_context
        with urlopen(config_url) as f:
            # oaf_config["live"] = json.load(f)
            if len(oaf_config["live"]) > 1:
                oaf_config["cache"] = oaf_config["live"]
                with open(config_file_path, "w") as fp:
                    json.dump(oaf_config["live"], fp)
    except Exception as e:
        print(
            "%sFailed to get config from %s %s"
            % (TERMINAL_COLOR_ERROR, config_url, TERMINAL_COLOR_NORMAL)
        )
        print("%s trace: %s %s" % (TERMINAL_COLOR_WARNING, e, TERMINAL_COLOR_NORMAL))

    if len(oaf_config["live"]) < 1 and os.path.exists(config_file_path):
        with open(config_file_path) as json_file:
            oaf_config["cache"] = json.load(json_file)

    if oaf_config["cache"] and len(oaf_config["live"]) < 1:
        oaf_config["cache"] = oaf_config["live"] = {
            "OAF_GIT_BRANCH_NAME_REGEX": "^((release\/[0-9]+\.[0-9]+\.[0-9])|((feature|feat|cleanup|bugfix|hotfix|fix|devops)\/[A-Z]+-[0-9]+(-[A-z0-9]+)+)|(umuganda|chore)\/[a-zA-Z0-9+\-]+)$",
            "OAF_WATCH_COMMIT_HISTORY": False,
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
                "ci",
                "build",
            ],
            "OAF_REQUIRED_HOOKS": {
                "ggshield": {
                    "args": ["--help"],
                    "repo": "https://github.com/gitguardian/ggshield",
                },
                "gitlint": {
                    "args": ["--help"],
                    "repo": "https://github.com/jorisroovers/gitlint",
                },
            },
        }
    return len(oaf_config)


def contains_config_directive(cfg, dir):
    return re.findall(dir, cfg, re.M)


def is_hook_installed(hook, args) -> bool:
    """Determine if the pre-commit hook is installed and enabled."""
    arg_str = " ".join(args)
    cmd = "pre-commit run " + hook + " " + arg_str + ""
    exit_code = os.WEXITSTATUS(os.system(cmd))
    exit_out = subprocess.getoutput(cmd)
    if exit_code != 0:
        print(
            "%s %s: code %d output %s %s"
            % (TERMINAL_COLOR_WARNING, cmd, exit_code, exit_out, TERMINAL_COLOR_NORMAL)
        )
    return exit_code == 0


def get_current_branch_name() -> str:
    """Determine the active Git branch name."""
    return subprocess.getoutput("git rev-parse --abbrev-ref HEAD")


def get_git_branch_name_regex() -> str:
    """Read Git and GitFlow naming Regex"""
    if len(oaf_config["cache"]) < 1:
        load_config()
    return oaf_config["cache"]["OAF_GIT_BRANCH_NAME_REGEX"]


def get_git_branch_name_exceptions() -> list:
    """Determine Git branches that are exempt from naming convention"""

    if len(oaf_config["cache"]) < 1:
        load_config()

    return oaf_config["cache"]["OAF_GIT_BRANCH_NAME_EXCEPTION"]


def get_git_conventional_commit_types() -> list:
    """Determine Git conventional commit types"""
    if len(oaf_config["cache"]) < 1:
        load_config()

    return oaf_config["cache"]["OAF_GIT_COMMIT_TYPES"]


def validate_git_commit(commit) -> bool:
    """Parse and verify git commit format"""
    commit_title = commit["title"].split(":")
    if len(commit_title) == 1:
        print(
            "%sCommit %s has invalid message `%s` %s"
            % (
                TERMINAL_COLOR_WARNING,
                commit["hash"],
                commit["title"],
                TERMINAL_COLOR_NORMAL,
            )
        )
        return False

    is_commit_ok = False
    oaf_commit_types = get_git_conventional_commit_types()
    commit_type = commit_title[0].split("(")[0]
    try:
        is_commit_ok = oaf_commit_types.index(commit_type) >= 0
    except ValueError:
        print(
            "%sCommit %s '%s' has wrong type `%s` %s"
            % (
                TERMINAL_COLOR_WARNING,
                commit["hash"],
                commit["title"],
                commit_type,
                TERMINAL_COLOR_NORMAL,
            )
        )
        return False

    return is_commit_ok


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
    parser.add_argument("--forced", default="False", help="check README.md")

    args, unknown_args = parser.parse_known_args(argv)
    print(
        "%s %2d files to check %s"
        % (TERMINAL_COLOR_PASS, len(unknown_args), TERMINAL_COLOR_NORMAL)
    )

    if len(sys.argv) == 1:
        print("How to pass args when calling the script:")
        parser.print_help()

    if args.forced == "False":
        load_config()
        for hook in oaf_config["cache"]["OAF_REQUIRED_HOOKS"]:
            hook_info = oaf_config["cache"]["OAF_REQUIRED_HOOKS"][hook]
            if is_hook_installed(hook, hook_info["args"]) == False:
                print(
                    "%s hook %s is not installed or is disabled %s see more:%s"
                    % (
                        TERMINAL_COLOR_ERROR,
                        hook,
                        hook_info["repo"],
                        TERMINAL_COLOR_NORMAL,
                    )
                )
                return 1

    # validate branch naming
    branch = get_current_branch_name()
    is_branch_lts = False
    is_branch_ok = False
    oaf_lts_branches = get_git_branch_name_exceptions()
    try:
        is_branch_lts = is_branch_ok = oaf_lts_branches.index(branch) >= 0
    except ValueError:
        pass
    if is_branch_lts == False:
        oaf_regex = get_git_branch_name_regex()
        is_branch_ok = re.search(oaf_regex, branch)

    if is_branch_ok == False:
        print(
            "%s branch %s name should follow {prefix/JIRA#-descr}:"
            "prefix=%s %s"
            % (
                TERMINAL_COLOR_WARNING,
                branch,
                ",".join(oaf_lts_branches),
                TERMINAL_COLOR_NORMAL,
            )
        )
        return 2

    # check commit history on this branch
    commits = get_commits()
    for commit in commits:
        is_commit_ok = validate_git_commit(commit)
        if is_commit_ok == False and is_branch_lts == False:
            if len(oaf_config) < 1:
                load_config()
                if oaf_config["OAF_WATCH_COMMIT_HISTORY"]:
                    return 3

    # check current commit message (e.g. prepare-commit-msg) using gitlint
    load_config()
    hook_info = oaf_config["cache"]["OAF_REQUIRED_HOOKS"]["gitlint"]
    if is_hook_installed(hook, hook_info["args"]):
        # check on .gitlint
        gitlint_path = subprocess.getoutput("git rev-parse --show-toplevel")
        gitlint_path += "/.gitlint"
        try:
            if os.path.exists(gitlint_path) == False:
                print(
                    "%s .gitlint is not found at gitlint_path %s %s"
                    % (TERMINAL_COLOR_ERROR, gitlint_path, TERMINAL_COLOR_NORMAL)
                )
                gitlint_url = "https://raw.githubusercontent.com/one-acre-fund/oaf-pre-commit-hooks/main/.gitlint"
                ssl._create_default_https_context = ssl._create_unverified_context
                with urlopen(gitlint_url) as gitlint_file:
                    gitlint_config = str(gitlint_file.read(), "UTF-8")
                    f = open(gitlint_path, "w")
                    f.write(gitlint_config)
                    f.close()
            else:
                keywords = [
                    "contrib=contrib-title-conventional-commits",
                    "types=",
                    "title-min-length",
                    "title-max-length",
                    "body-max-line-length",
                ]
                gitlint_file = open(gitlint_path, "r")
                gitlint_config = gitlint_file.read()
                for keyword in keywords:
                    matching_regex = contains_config_directive(gitlint_config, keyword)
                    if len(matching_regex) < 1:
                        print(
                            "%s .gitlint is missing important rules %s %s %s"
                            % (
                                TERMINAL_COLOR_ERROR,
                                gitlint_path,
                                gitlint_config,
                                TERMINAL_COLOR_NORMAL,
                            )
                        )
                        gitlint_file.close()
                        return 4
        except Exception as e:
            print(
                "%sFailed to read .gitlint config from %s : %s %s"
                % (TERMINAL_COLOR_ERROR, gitlint_path, e, TERMINAL_COLOR_NORMAL)
            )
            return 4


if __name__ == "__main__":
    raise SystemExit(main())

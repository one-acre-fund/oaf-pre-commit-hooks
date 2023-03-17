#!/usr/bin/env python3
"""Helper script to be used as a pre-commit hook."""
import argparse
import os
import re
import ssl
import subprocess
import sys
import warnings
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
            oaf_config["live"] = json.load(f)
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
            "OAF_WATCH_COMMIT_HISTORY": False,
        }
    print(oaf_config)
    return len(oaf_config)


def is_hook_installed(hook) -> bool:
    """Determine if the pre-commit hook is installed and enabled."""
    exit_code = os.WEXITSTATUS(os.system("git config --bool " + hook))
    out = subprocess.getoutput("git config --bool " + hook)
    return exit_code == 0 and out == "false"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="", help="check README.md")
    parser.add_argument("--forced", default=True, help="check README.md")
    parser.add_argument("--verbose", default=True, help="Verbose debug logging.")
    args, unknown_args = parser.parse_known_args(argv)

    if args.verbose:
        print(
            "%s %2d files to check %s"
            % (TERMINAL_COLOR_PASS, len(unknown_args), TERMINAL_COLOR_NORMAL)
        )
        print(args, unknown_args)

    if len(sys.argv) == 1:
        print("How to pass args when calling the script:")
        parser.print_help()

    if (
        args.forced == False
        and is_hook_installed("hooks.oaf-pre-commit-hook-git-commit") == False
    ):
        print(
            "%sHook is not installed or disabled:(enable with 'git config hooks.oaf-pre-commit-hook-git-branch true') %s"
            % (TERMINAL_COLOR_ERROR, TERMINAL_COLOR_NORMAL)
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

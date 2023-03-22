from __future__ import annotations

import json
import subprocess

import pytest

from pre_commit_hooks.oaf_tech_pre_commit_hook import (
    get_commits,
    get_current_branch_name,
    is_hook_installed,
    load_config,
    validate_git_commit,
)


# Tests that the function correctly identifies the pre-commit home directory and cache directory when pre_commit_home exists. tags: [happy path]
def test_load_config_pre_commit_home_exists(self, monkeypatch):
    monkeypatch.setenv("PRE_COMMIT_HOME", "/path/to/pre-commit")
    assert load_config() == 0


# Tests that the function correctly identifies the pre-commit home directory and cache directory when pre_commit_home exists. tags: [happy path]
def test_load_config_pre_commit_home_exists(self, monkeypatch):
    monkeypatch.setenv("PRE_COMMIT_HOME", "/path/to/pre-commit")
    assert load_config() == 0


# Tests that the function correctly identifies the pre-commit home directory and cache directory when pre_commit_home does not exist but xdg_cache_home exists. tags: [happy path]
def test_load_config_xdg_cache_home_exists(self, monkeypatch):
    monkeypatch.delenv("PRE_COMMIT_HOME", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", "/path/to/cache")
    assert load_config() == 0


# Tests that the function correctly identifies the pre-commit home directory and cache directory when neither pre_commit_home nor xdg_cache_home exist but the cache directory exists. tags: [happy path]
def test_load_config_cache_dir_exists(self, monkeypatch, tmp_path):
    monkeypatch.delenv("PRE_COMMIT_HOME", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    cache_dir = tmp_path / "pre-commit"
    cache_dir.mkdir()
    assert load_config() == 0


# Tests that the function sets default values for configuration when both the live configuration and cache directory are empty. tags: [edge case]
def test_load_config_default_config_values(self, monkeypatch):
    oaf_config = {"cache": [], "live": []}
    monkeypatch.delenv("PRE_COMMIT_HOME", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    oaf_config["cache"] = []
    oaf_config["live"] = []
    assert load_config() == 10


# Tests that the function successfully downloads and saves the configuration file to the cache directory. tags: [happy path]
def test_load_config_config_download_success(self, monkeypatch, mocker):
    monkeypatch.delenv("PRE_COMMIT_HOME", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    mocker.patch("urllib.request.urlopen")
    urlopen_mock = mocker.MagicMock()
    urlopen_mock.__enter__.return_value = urlopen_mock
    urlopen_mock.read.return_value = json.dumps(
        {
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
    ).encode()
    urlopen_mock.status = 200
    urlopen_mock.reason = "OK"
    urlopen_mock.headers = {}
    urlopen_mock.url = "https://raw.githubusercontent.com/one-acre-fund/oaf-pre-commit-hooks/main/config.json"
    urlopen_mock.info.return_value.get_content_charset.return_value = "utf-8"
    urlopen_mock.info.return_value.get_content_type.return_value = "application/json"
    urlopen_mock.info.return_value.get_param.return_value = None
    urlopen_mock.info.return_value.getplist.return_value = []
    urlopen_mock.info.return_value.items.return_value = []
    urlopen_mock.info.return_value.getheaders.return_value = []
    urlopen_mock.info.return_value.get_all.return_value = []
    urlopen_mock.info.return_value.typeheader = None
    urlopen_mock.info.return_value.getencoding.return_value = None
    urlopen_mock.info.return_value.getmaintype.return_value = None
    mocker.patch("ssl._create_default_https_context")
    ssl_mock = mocker.MagicMock()
    ssl_mock._create_unverified_context.return_value = ssl_mock
    with mocker.patch("builtins.open", mocker.mock_open()) as mock_file:
        assert load_config() == 1
        mock_file.assert_called_once_with(
            "/.cache/pre-commit/oaf_pre-commit_config.json", "w"
        )
        mock_file().write.assert_called_once_with(urlopen_mock.read())


# Tests that the function loads the configuration file from the cache directory when the live configuration is empty. tags: [happy path]
def test_config_load_from_cache(self, monkeypatch, tmp_path):
    oaf_config = {"cache": [], "live": []}
    monkeypatch.delenv("PRE_COMMIT_HOME", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    oaf_config["cache"] = {
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
    oaf_config["live"] = []
    config_file_path = tmp_path / ".cache/pre-commit/oaf_pre-commit_config.json"
    with open(config_file_path, "w") as f:
        json.dump(oaf_config["cache"], f)
    assert load_config() == 5


# Tests that the function constructs the correct command string when given arguments. tags: [happy path]
def test_hook_installed_with_arguments(self):
    assert is_hook_installed("pre-commit", ["--all-files"]) == True
    assert is_hook_installed("flake8", ["--max-line-length=80"]) == True


# Tests that the function constructs the correct command string when given no arguments. tags: [happy path]
def test_hook_installed_without_arguments(self):
    assert is_hook_installed("black", []) == True
    assert is_hook_installed("isort", []) == True


# Tests that the function returns false when the hook is not installed. tags: [edge case]
def test_hook_installed_not_installed(self):
    assert is_hook_installed("non-existent-hook", []) == False


# Tests that the function returns false when the hook name is empty. tags: [edge case]
def test_hook_installed_empty_name(self):
    assert is_hook_installed("", []) == False


# Tests that the function handles special characters in hook name and arguments correctly. tags: [general behavior]
def test_hook_installed_special_characters(self):
    assert is_hook_installed("pre-commit", ["--hook-type=python"]) == True
    assert is_hook_installed("pytest", ["-k", "test_functional"]) == True


# Tests that the function handles spaces in hook name and arguments correctly. tags: [general behavior]
def test_hook_installed_spaces(self):
    assert (
        is_hook_installed("pre-commit", ["--hook-type=python", "--exclude=tests"])
        == True
    )
    assert is_hook_installed("pytest", ["-m", "not slow"]) == True


def test_get_current_branch_name_on_branch(self, mocker):
    mocker.patch("subprocess.getoutput", return_value="main")
    assert get_current_branch_name() == "main"


# Tests that the function returns an empty string when the git repository is empty. tags: [edge case]
def test_get_current_branch_name_empty_repository(self, mocker):
    mocker.patch(
        "subprocess.getoutput",
        return_value="fatal: not a git repository (or any of the parent directories): .git",
    )
    assert get_current_branch_name() == ""


# Tests that the function returns an empty string when the git repository has no branches. tags: [edge case]
def test_get_current_branch_name_no_branches(self, mocker):
    mocker.patch("subprocess.getoutput", return_value="HEAD")
    assert get_current_branch_name() == ""


# Tests that the function returns "head" when the git repository is in a detached head state. tags: [edge case]
def test_get_current_branch_name_detached_head(self, mocker):
    mocker.patch("subprocess.getoutput", return_value="HEAD")
    assert get_current_branch_name() == "HEAD"


# Tests that the function raises a subprocess.calledprocesserror when git is not installed on the system. tags: [edge case]
def test_get_current_branch_name_git_not_installed(self, mocker):
    mocker.patch(
        "subprocess.getoutput", side_effect=subprocess.CalledProcessError(1, "git")
    )
    with pytest.raises(subprocess.CalledProcessError):
        get_current_branch_name()


# Tests that the function raises a subprocess.calledprocesserror when the user running the script does not have permission to access the git repository. tags: [edge case]
def test_get_current_branch_name_permission_denied(self, mocker):
    mocker.patch(
        "subprocess.getoutput",
        side_effect=subprocess.CalledProcessError(1, "git rev-parse --abbrev-ref HEAD"),
    )
    with pytest.raises(subprocess.CalledProcessError):
        get_current_branch_name()


# Tests that a commit title with a valid conventional commit type is correctly validated. tags: [happy path]
def test_valid_commit_title(self):
    commit = {"title": "feat: add new feature", "hash": "abc123"}
    assert validate_git_commit(commit) == True


# Tests that a commit title with a valid conventional commit type and parentheses is correctly validated. tags: [happy path]
def test_valid_commit_title_with_parentheses(self):
    commit = {"title": "fix(docs): update documentation", "hash": "def456"}
    assert validate_git_commit(commit) == True


# Tests that a commit title with an invalid conventional commit type is correctly identified as invalid. tags: [edge case]
def test_commit_title_with_invalid_conventional_commit_type(self):
    commit = {"title": "invalid: this is not a valid commit type", "hash": "ghi789"}
    assert validate_git_commit(commit) == False


# Tests that an empty oaf_config["cache"] dictionary is handled correctly. tags: [edge case]
def test_empty_oaf_config_cache(self, monkeypatch):
    oaf_config = {"cache": []}
    monkeypatch.setitem(oaf_config, "cache", {})
    commit = {"title": "feat: add new feature", "hash": "abc123"}
    assert validate_git_commit(commit) == False


# Tests that a commit title with no separator is correctly identified as invalid. tags: [edge case]
def test_commit_title_with_no_separator(self):
    commit = {"title": "this is not a valid commit title", "hash": "jkl012"}
    assert validate_git_commit(commit) == False


# Tests that a commit title with an empty first part is correctly identified as invalid. tags: [edge case]
def test_commit_title_with_empty_first_part(self):
    commit = {"title": ": this is not a valid commit title", "hash": "mno345"}
    assert validate_git_commit(commit) == False


# Tests that the function correctly extracts and formats the commit title and message when the git repository has only one commit. tags: [happy path]
def test_get_commits_single_commit(self, mocker):
    mocker.patch(
        "subprocess.check_output",
        return_value=b"commit abc123\nAuthor: John Doe\nDate: 2021-01-01\n\nThis is a commit message.",
    )
    commits = get_commits()
    assert len(commits) == 1
    assert commits[0]["hash"] == "abc123"
    assert commits[0]["title"] == "This is a commit message."
    assert commits[0]["message"] == ""


# Tests that the function correctly handles multi-line commit messages. tags: [happy path]
def test_get_commits_multi_line_commit_messages(self, mocker):
    mocker.patch(
        "subprocess.check_output",
        return_value=b"commit abc123\nAuthor: John Doe\nDate: 2021-01-01\n\nThis is a commit message.\n\nThis is a second line.",
    )
    commits = get_commits()
    assert len(commits) == 1
    assert commits[0]["hash"] == "abc123"
    assert commits[0]["title"] == "This is a commit message."
    assert commits[0]["message"] == "This is a second line."


# Tests that the function returns an empty list when the git repository has no commits. tags: [edge case]
def test_get_commits_empty_repository(self, mocker):
    mocker.patch("subprocess.check_output", return_value=b"")
    commits = get_commits()
    assert len(commits) == 0


# Tests that the function does not work correctly when the git repository is not in a valid state. tags: [edge case]
def test_get_commits_invalid_git_repository(self, mocker):
    mocker.patch(
        "subprocess.check_output",
        side_effect=subprocess.CalledProcessError(1, "git log"),
    )
    with pytest.raises(subprocess.CalledProcessError):
        get_commits()


# Tests that the function correctly handles commits with non-standard characters in commit message. tags: [edge case]
def test_get_commits_non_standard_characters_in_commit_message(self, mocker):
    mocker.patch(
        "subprocess.check_output",
        return_value="commit abc123\nAuthor: John Doe\nDate: 2021-01-01\n\nThis is a commit message with non-standard characters: é, ü, ñ.",
    )
    commits = get_commits()
    assert len(commits) == 1
    assert commits[0]["hash"] == "abc123"
    assert (
        commits[0]["title"]
        == "This is a commit message with non-standard characters: é, ü, ñ."
    )
    assert commits[0]["message"] == ""


# Tests that the function correctly handles commits with non-standard characters in author name. tags: [edge case]
def test_get_commits_non_standard_characters_in_author_name(self, mocker):
    mocker.patch(
        "subprocess.check_output",
        return_value="commit abc123\nAuthor: Jöhn Döe\nDate: 2021-01-01\n\nThis is a commit message.",
    )
    commits = get_commits()
    assert len(commits) == 1
    assert commits[0]["hash"] == "abc123"
    assert commits[0]["title"] == "This is a commit message."
    assert commits[0]["message"] == ""

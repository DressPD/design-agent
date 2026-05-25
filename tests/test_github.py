import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from src.tools.github import github_create_and_push, _push_to_existing


@pytest.fixture
def existing_project(tmp_path):
    project = tmp_path / "my-app"
    project.mkdir()
    (project / "index.html").write_text("<html></html>")
    return project


def make_run_result(returncode=0, stdout="", stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


class TestGithubCreateAndPush:
    def test_returns_error_when_path_missing(self):
        result = github_create_and_push("my-repo", "/nonexistent/path")
        data = json.loads(result)
        assert "error" in data
        assert "/nonexistent/path" in data["error"]

    def test_success_returns_repo_url_and_name(self, existing_project):
        ok = make_run_result(returncode=0, stdout="https://github.com/user/my-repo\n")
        with patch("src.tools.github.subprocess.run", return_value=ok):
            result = github_create_and_push("my-repo", str(existing_project))
        data = json.loads(result)
        assert data["repo_name"] == "my-repo"
        assert data["push_status"] == "success"

    def test_calls_gh_repo_create_with_private_flag(self, existing_project):
        ok = make_run_result(returncode=0, stdout="https://github.com/user/my-repo\n")
        with patch("src.tools.github.subprocess.run", return_value=ok) as mock_run:
            github_create_and_push("my-repo", str(existing_project), private=True)
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "--private" in first_call_args

    def test_calls_gh_repo_create_with_public_flag(self, existing_project):
        ok = make_run_result(returncode=0, stdout="https://github.com/user/my-repo\n")
        with patch("src.tools.github.subprocess.run", return_value=ok) as mock_run:
            github_create_and_push("my-repo", str(existing_project), private=False)
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "--public" in first_call_args

    def test_falls_back_to_push_existing_when_repo_exists(self, existing_project):
        already_exists = make_run_result(returncode=1, stderr="already exists on GitHub")
        view_result = make_run_result(returncode=0, stdout="https://github.com/user/my-repo\n")
        git_ok = make_run_result(returncode=0)
        push_ok = make_run_result(returncode=0)
        side_effects = [already_exists, view_result, git_ok, git_ok, git_ok, git_ok, push_ok]
        with patch("src.tools.github.subprocess.run", side_effect=side_effects):
            result = github_create_and_push("my-repo", str(existing_project))
        data = json.loads(result)
        assert "push_status" in data
        assert "existing" in data["push_status"]

    def test_returns_error_on_gh_create_failure(self, existing_project):
        fail = make_run_result(returncode=1, stderr="some other error")
        with patch("src.tools.github.subprocess.run", return_value=fail):
            result = github_create_and_push("my-repo", str(existing_project))
        data = json.loads(result)
        assert "error" in data

    def test_fetches_repo_url_when_stdout_not_http(self, existing_project):
        create_ok = make_run_result(returncode=0, stdout="not-a-url\n")
        view_ok = make_run_result(returncode=0, stdout="https://github.com/user/my-repo\n")
        with patch("src.tools.github.subprocess.run", side_effect=[create_ok, view_ok]):
            result = github_create_and_push("my-repo", str(existing_project))
        data = json.loads(result)
        assert data["repo_url"] == "https://github.com/user/my-repo"


class TestPushToExisting:
    def test_success_returns_correct_status(self, existing_project):
        view_ok = make_run_result(returncode=0, stdout="https://github.com/user/my-repo\n")
        git_ok = make_run_result(returncode=0)
        push_ok = make_run_result(returncode=0)
        side_effects = [view_ok, git_ok, git_ok, git_ok, git_ok, push_ok]
        with patch("src.tools.github.subprocess.run", side_effect=side_effects):
            result = _push_to_existing("my-repo", existing_project)
        data = json.loads(result)
        assert data["push_status"] == "success (force-pushed to existing)"
        assert data["repo_name"] == "my-repo"

    def test_returns_error_on_push_failure(self, existing_project):
        view_ok = make_run_result(returncode=0, stdout="https://github.com/user/my-repo\n")
        git_ok = make_run_result(returncode=0)
        push_fail = make_run_result(returncode=1, stderr="push rejected")
        side_effects = [view_ok, git_ok, git_ok, git_ok, git_ok, push_fail]
        with patch("src.tools.github.subprocess.run", side_effect=side_effects):
            result = _push_to_existing("my-repo", existing_project)
        data = json.loads(result)
        assert "error" in data
        assert data["error"] == "git push failed"

    def test_calls_git_init_and_add(self, existing_project):
        view_ok = make_run_result(returncode=0, stdout="https://github.com/user/my-repo\n")
        git_ok = make_run_result(returncode=0)
        push_ok = make_run_result(returncode=0)
        side_effects = [view_ok, git_ok, git_ok, git_ok, git_ok, push_ok]
        with patch("src.tools.github.subprocess.run", side_effect=side_effects) as mock_run:
            _push_to_existing("my-repo", existing_project)
        all_cmds = [c[0][0] for c in mock_run.call_args_list]
        assert any("git" in cmd and "init" in cmd for cmd in all_cmds)
        assert any("git" in cmd and "add" in cmd for cmd in all_cmds)

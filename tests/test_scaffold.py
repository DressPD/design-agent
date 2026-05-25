import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from src.tools.scaffold import scaffold_react_app, _write_package_json


SAMPLE_COMPONENTS = json.dumps([
    {"name": "Hero", "code": "export default function Hero() { return <div>Hero</div> }"},
    {"name": "Footer", "code": "export default function Footer() { return <footer>Footer</footer> }"},
])


@pytest.fixture
def mock_subprocess_success():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    with patch("src.tools.scaffold.subprocess.run", return_value=mock_result) as m:
        yield m


@pytest.fixture
def project_path(tmp_path):
    return tmp_path / "test-project"


class TestScaffoldReactApp:
    def test_creates_project_directory(self, mock_subprocess_success, tmp_path):
        with patch("src.tools.scaffold.Path") as mock_path_cls:
            real_path = tmp_path / "myapp"
            mock_path_cls.return_value = real_path
            with patch("src.tools.scaffold.shutil.rmtree"):
                result = scaffold_react_app("myapp", SAMPLE_COMPONENTS)
        data = json.loads(result)
        assert "project_path" in data

    def test_returns_success_json(self, mock_subprocess_success, tmp_path):
        target = tmp_path / "myapp"
        with patch("src.tools.scaffold.Path", side_effect=lambda p: tmp_path / Path(p).name if "/tmp/design-agent-builds/" in str(p) else Path(p)):
            result = scaffold_react_app("myapp", SAMPLE_COMPONENTS)
        data = json.loads(result)
        assert data["build_status"] == "success"
        assert data["component_count"] == 2

    def test_calls_npm_install(self, mock_subprocess_success, tmp_path):
        with patch("src.tools.scaffold.Path", side_effect=lambda p: tmp_path / Path(p).name if "/tmp/design-agent-builds/" in str(p) else Path(p)):
            scaffold_react_app("myapp", SAMPLE_COMPONENTS)
        calls = mock_subprocess_success.call_args_list
        npm_install_call = next((c for c in calls if "npm" in c[0][0] and "install" in c[0][0]), None)
        assert npm_install_call is not None

    def test_calls_npm_build(self, mock_subprocess_success, tmp_path):
        with patch("src.tools.scaffold.Path", side_effect=lambda p: tmp_path / Path(p).name if "/tmp/design-agent-builds/" in str(p) else Path(p)):
            scaffold_react_app("myapp", SAMPLE_COMPONENTS)
        calls = mock_subprocess_success.call_args_list
        build_call = next((c for c in calls if "npm" in c[0][0] and "build" in c[0][0]), None)
        assert build_call is not None

    def test_npm_install_failure_returns_error(self, tmp_path):
        fail_result = MagicMock()
        fail_result.returncode = 1
        fail_result.stderr = "npm ERR! some error"
        with patch("src.tools.scaffold.subprocess.run", return_value=fail_result):
            with patch("src.tools.scaffold.Path", side_effect=lambda p: tmp_path / Path(p).name if "/tmp/design-agent-builds/" in str(p) else Path(p)):
                result = scaffold_react_app("myapp", SAMPLE_COMPONENTS)
        data = json.loads(result)
        assert "error" in data
        assert data["error"] == "npm install failed"

    def test_npm_build_failure_returns_error(self, tmp_path):
        install_ok = MagicMock(returncode=0, stderr="", stdout="")
        build_fail = MagicMock(returncode=1, stderr="build error output", stdout="")
        with patch("src.tools.scaffold.subprocess.run", side_effect=[install_ok, build_fail]):
            with patch("src.tools.scaffold.Path", side_effect=lambda p: tmp_path / Path(p).name if "/tmp/design-agent-builds/" in str(p) else Path(p)):
                result = scaffold_react_app("myapp", SAMPLE_COMPONENTS)
        data = json.loads(result)
        assert "error" in data
        assert data["error"] == "build failed"

    def test_accepts_components_as_list(self, mock_subprocess_success, tmp_path):
        components_list = [
            {"name": "Hero", "code": "export default function Hero() {}"},
        ]
        with patch("src.tools.scaffold.Path", side_effect=lambda p: tmp_path / Path(p).name if "/tmp/design-agent-builds/" in str(p) else Path(p)):
            result = scaffold_react_app("myapp", components_list)
        data = json.loads(result)
        assert data["component_count"] == 1


class TestWritePackageJson:
    def test_package_json_has_correct_name(self, tmp_path):
        _write_package_json(tmp_path, "my-cool-app")
        pkg = json.loads((tmp_path / "package.json").read_text())
        assert pkg["name"] == "my-cool-app"

    def test_package_json_has_react_dependency(self, tmp_path):
        _write_package_json(tmp_path, "app")
        pkg = json.loads((tmp_path / "package.json").read_text())
        assert "react" in pkg["dependencies"]
        assert "react-dom" in pkg["dependencies"]

    def test_package_json_has_vite_scripts(self, tmp_path):
        _write_package_json(tmp_path, "app")
        pkg = json.loads((tmp_path / "package.json").read_text())
        assert "dev" in pkg["scripts"]
        assert "build" in pkg["scripts"]

    def test_package_json_has_tailwind_devdep(self, tmp_path):
        _write_package_json(tmp_path, "app")
        pkg = json.loads((tmp_path / "package.json").read_text())
        assert "tailwindcss" in pkg["devDependencies"]

    def test_package_json_is_module_type(self, tmp_path):
        _write_package_json(tmp_path, "app")
        pkg = json.loads((tmp_path / "package.json").read_text())
        assert pkg["type"] == "module"

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import src.config as config_module
from src.config import get_api_key, _parse_env_file, get_google_api_key, get_twentyfirst_api_key


class TestParseEnvFile:
    def test_returns_empty_dict_when_file_missing(self, tmp_path):
        result = _parse_env_file(tmp_path / "nonexistent.env")
        assert result == {}

    def test_parses_simple_key_value(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("MY_KEY=my_value\n")
        assert _parse_env_file(env_file) == {"MY_KEY": "my_value"}

    def test_skips_comment_lines(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# this is a comment\nFOO=bar\n")
        assert _parse_env_file(env_file) == {"FOO": "bar"}

    def test_skips_empty_lines(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("\n\nFOO=bar\n\n")
        assert _parse_env_file(env_file) == {"FOO": "bar"}

    def test_strips_double_quotes(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text('API_KEY="secret123"\n')
        assert _parse_env_file(env_file) == {"API_KEY": "secret123"}

    def test_strips_single_quotes(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY='secret123'\n")
        assert _parse_env_file(env_file) == {"API_KEY": "secret123"}

    def test_skips_lines_without_equals(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("INVALID_LINE\nFOO=bar\n")
        assert _parse_env_file(env_file) == {"FOO": "bar"}

    def test_value_with_equals_sign(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("TOKEN=abc=def=ghi\n")
        assert _parse_env_file(env_file) == {"TOKEN": "abc=def=ghi"}

    def test_multiple_keys(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=val1\nKEY2=val2\nKEY3=val3\n")
        assert _parse_env_file(env_file) == {"KEY1": "val1", "KEY2": "val2", "KEY3": "val3"}

    def test_strips_whitespace_around_key(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("  MY_KEY  =  my_value  \n")
        assert _parse_env_file(env_file) == {"MY_KEY": "my_value"}


class TestGetApiKey:
    def test_returns_value_from_env_var(self, monkeypatch):
        monkeypatch.setenv("MY_API_KEY", "from-env")
        assert get_api_key("MY_API_KEY") == "from-env"

    def test_falls_back_to_env_file(self, monkeypatch, tmp_path):
        monkeypatch.delenv("MY_API_KEY", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text("MY_API_KEY=from-file\n")
        with patch.object(config_module, "_PROJECT_ENV_FILE", env_file):
            assert get_api_key("MY_API_KEY") == "from-file"

    def test_raises_key_error_when_not_found(self, monkeypatch, tmp_path):
        monkeypatch.delenv("MY_API_KEY", raising=False)
        missing_file = tmp_path / "missing.env"
        with patch.object(config_module, "_PROJECT_ENV_FILE", missing_file):
            with pytest.raises(KeyError, match="MY_API_KEY"):
                get_api_key("MY_API_KEY")

    def test_env_var_takes_priority_over_file(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MY_API_KEY", "from-env")
        env_file = tmp_path / ".env"
        env_file.write_text("MY_API_KEY=from-file\n")
        with patch.object(config_module, "_PROJECT_ENV_FILE", env_file):
            assert get_api_key("MY_API_KEY") == "from-env"

    def test_get_google_api_key_uses_correct_name(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "google-key-123")
        assert get_google_api_key() == "google-key-123"

    def test_get_twentyfirst_api_key_uses_correct_name(self, monkeypatch):
        monkeypatch.setenv("TWENTYFIRST_API_KEY", "21st-key-456")
        assert get_twentyfirst_api_key() == "21st-key-456"

    def test_error_message_includes_key_name(self, monkeypatch, tmp_path):
        monkeypatch.delenv("SPECIAL_KEY", raising=False)
        missing_file = tmp_path / "missing.env"
        with patch.object(config_module, "_PROJECT_ENV_FILE", missing_file):
            with pytest.raises(KeyError) as exc_info:
                get_api_key("SPECIAL_KEY")
            assert "SPECIAL_KEY" in str(exc_info.value)

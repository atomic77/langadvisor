"""Tests for cross-platform path resolution."""

from unittest.mock import patch

from core.paths import config_dir, data_dir


class TestPaths:
    @patch("core.paths.Path.mkdir")
    @patch("core.paths.user_data_dir")
    def test_data_dir_returns_path(self, mock_user_data_dir, mock_mkdir):
        mock_user_data_dir.return_value = "/fake/data/langadvisor"
        path = data_dir()
        assert str(path) == "/fake/data/langadvisor"
        mock_user_data_dir.assert_called_once_with("langadvisor")
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("core.paths.Path.mkdir")
    @patch("core.paths.user_config_dir")
    def test_config_dir_returns_path(self, mock_user_config_dir, mock_mkdir):
        mock_user_config_dir.return_value = "/fake/config/langadvisor"
        path = config_dir()
        assert str(path) == "/fake/config/langadvisor"
        mock_user_config_dir.assert_called_once_with("langadvisor")
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

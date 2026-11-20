import json
from unittest.mock import MagicMock, patch
import pytest

from drill.adapters.restic import ResticAdapter


def test_get_latest_snapshot_returns_first_item(tmp_path):
    # Verify snapshot JSON parsing and RESTIC_REPOSITORY/RESTIC_PASSWORD env setup
    adapter = ResticAdapter(
        repository=str(tmp_path / "repo"),
        password="secret",
        destination=str(tmp_path / "restore"),
    )
    sample_snapshots = [{"id": "abc12345", "time": "2026-11-20T10:00:00Z"}]

    with patch("subprocess.run", return_value=MagicMock(stdout=json.dumps(sample_snapshots))) as mock_run:
        snap = adapter.get_latest_snapshot()
        assert snap["id"] == "abc12345"
        called_env = mock_run.call_args.kwargs["env"]
        assert called_env["RESTIC_PASSWORD"] == "secret"
        assert called_env["RESTIC_REPOSITORY"] == str((tmp_path / "repo").resolve())


def test_get_latest_snapshot_raises_when_empty(tmp_path):
    # Empty snapshot list should raise RuntimeError
    adapter = ResticAdapter(
        repository=str(tmp_path / "repo"),
        password="secret",
        destination=str(tmp_path / "restore"),
    )
    with patch("subprocess.run", return_value=MagicMock(stdout="[]")):
        with pytest.raises(RuntimeError, match="No snapshots found"):
            adapter.get_latest_snapshot()


def test_execute_restore_counts_restored_files(tmp_path):
    # Simulate restic creating restored files inside the target directory
    dest = tmp_path / "restore_target"
    adapter = ResticAdapter(
        repository=str(tmp_path / "repo"),
        password="secret",
        destination=str(dest),
    )

    def fake_restore(*args, **kwargs):
        file_path = dest / "data" / "app.db"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("ok")
        return MagicMock(returncode=0, stderr="")

    with patch("subprocess.run", side_effect=fake_restore):
        summary = adapter.execute_restore(snapshot_id="latest")
        assert summary["restored_files_count"] == 1
        assert summary["target_path"] == str(dest)
        assert summary["duration_seconds"] >= 0.0


def test_execute_restore_raises_on_nonzero_exit(tmp_path):
    # Non-zero exit from restic should raise RuntimeError with stderr
    adapter = ResticAdapter(
        repository=str(tmp_path / "repo"),
        password="wrong",
        destination=str(tmp_path / "restore"),
    )
    with patch("subprocess.run", return_value=MagicMock(returncode=1, stderr="wrong password")):
        with pytest.raises(RuntimeError, match="Restic restore failed"):
            adapter.execute_restore()

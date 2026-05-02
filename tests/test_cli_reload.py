import contextlib
import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import cli as yasb_cli  # noqa: E402


@contextlib.contextmanager
def _patched_cli(argv: list[str]):
    old_argv = sys.argv[:]
    sys.argv = argv
    try:
        yield
    finally:
        sys.argv = old_argv


def test_reload_uses_pipe_without_process_gate():
    calls: list[str] = []

    def fake_send(command: str):
        calls.append(command)

    def fail_if_called(_name: str):
        raise AssertionError("reload should not query packaged process state")

    handler = yasb_cli.CLIHandler()
    handler.send_command_to_application = fake_send  # type: ignore[method-assign]

    original_is_process_running = yasb_cli.is_process_running
    yasb_cli.is_process_running = fail_if_called  # type: ignore[assignment]
    try:
        with _patched_cli(["yasbc", "reload", "--silent"]):
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    handler.parse_arguments()
            except SystemExit as exc:
                assert exc.code == 0
            else:
                raise AssertionError("reload should exit")
    finally:
        yasb_cli.is_process_running = original_is_process_running

    assert calls == ["reload"]


if __name__ == "__main__":
    test_reload_uses_pipe_without_process_gate()
    print("yasb cli reload test passed")

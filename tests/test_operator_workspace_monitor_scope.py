import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.widgets.yasb.operator_workspaces import _screen_matches_monitor_scope  # noqa: E402


def test_all_monitor_workspace_highlights_on_every_screen():
    assert _screen_matches_monitor_scope(
        {"kind": "all_monitors"},
        "ROG PG279Q (1)",
        "left_or_secondary",
        0,
    )


def test_single_monitor_workspace_matches_left_to_right_index():
    scope = {
        "kind": "single_monitor",
        "observed_monitor_name": "DISPLAY1",
        "komorebi_monitor_index": 0,
        "monitor_role": "left_or_secondary",
    }

    assert _screen_matches_monitor_scope(scope, "ROG PG279Q (1)", "left_or_secondary", 0)
    assert not _screen_matches_monitor_scope(scope, "ROG PG279Q (2)", "right_or_primary", 1)


def test_single_monitor_workspace_matches_observed_display_name_when_available():
    scope = {
        "kind": "single_monitor",
        "observed_monitor_name": r"\\.\DISPLAY2",
        "komorebi_monitor_index": 1,
        "monitor_role": "right_or_primary",
    }

    assert _screen_matches_monitor_scope(scope, "DISPLAY2", "left_or_secondary", 0)


def test_single_monitor_workspace_falls_back_to_role():
    scope = {
        "kind": "single_monitor",
        "monitor_role": "right_or_primary",
    }

    assert _screen_matches_monitor_scope(scope, "ROG PG279Q (2)", "right_or_primary", None)
    assert not _screen_matches_monitor_scope(scope, "ROG PG279Q (1)", "left_or_secondary", None)


if __name__ == "__main__":
    test_all_monitor_workspace_highlights_on_every_screen()
    test_single_monitor_workspace_matches_left_to_right_index()
    test_single_monitor_workspace_matches_observed_display_name_when_available()
    test_single_monitor_workspace_falls_back_to_role()
    print("operator workspace monitor scope tests passed")

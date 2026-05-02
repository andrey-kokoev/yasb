import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.widgets.yasb.operator_workspaces import (  # noqa: E402
    _active_workspace_id_for_screen,
    _screen_matches_monitor_scope,
)


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


def test_active_workspace_can_be_different_per_monitor():
    workspaces = [
        {
            "workspace_id": "narada-andrey-left",
            "monitor_scope": {
                "kind": "single_monitor",
                "observed_monitor_name": "DISPLAY1",
                "komorebi_monitor_index": 0,
                "monitor_role": "left_or_secondary",
            },
        },
        {
            "workspace_id": "narada-proper-right",
            "monitor_scope": {
                "kind": "single_monitor",
                "observed_monitor_name": "DISPLAY2",
                "komorebi_monitor_index": 1,
                "monitor_role": "right_or_primary",
            },
        },
    ]
    active_by_monitor = {
        "DISPLAY1": "narada-andrey-left",
        "left_or_secondary": "narada-andrey-left",
        "komorebi_monitor_index:0": "narada-andrey-left",
        "DISPLAY2": "narada-proper-right",
        "right_or_primary": "narada-proper-right",
        "komorebi_monitor_index:1": "narada-proper-right",
    }

    assert (
        _active_workspace_id_for_screen(
            workspaces,
            "narada-proper-right",
            active_by_monitor,
            "ROG PG279Q (1)",
            "left_or_secondary",
            0,
        )
        == "narada-andrey-left"
    )
    assert (
        _active_workspace_id_for_screen(
            workspaces,
            "narada-andrey-left",
            active_by_monitor,
            "ROG PG279Q (2)",
            "right_or_primary",
            1,
        )
        == "narada-proper-right"
    )


if __name__ == "__main__":
    test_all_monitor_workspace_highlights_on_every_screen()
    test_single_monitor_workspace_matches_left_to_right_index()
    test_single_monitor_workspace_matches_observed_display_name_when_available()
    test_single_monitor_workspace_falls_back_to_role()
    test_active_workspace_can_be_different_per_monitor()
    print("operator workspace monitor scope tests passed")

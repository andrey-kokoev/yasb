import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.widgets.yasb.operator_workspaces import OperatorWorkspacesWidget  # noqa: E402


class _MockConfig:
    selector_projection_path = ""
    workspace_state_path = ""
    runtime_state_path = ""


class _MockWidget(OperatorWorkspacesWidget):
    def __init__(self, projection_path: str, workspaces: list[dict]):
        self.config = _MockConfig()
        self.config.selector_projection_path = projection_path
        self.config.workspace_state_path = ""
        self.config.runtime_state_path = ""
        self.screen_name = None
        self._mock_workspaces = workspaces

    def _screen_context_signature(self):
        return ("DISPLAY2", "right_or_primary", 1)

    def _load_json(self, path: str) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def test_selector_projection_includes_launchable_workspaces():
    with TemporaryDirectory() as tmp:
        projection_path = Path(tmp) / "selector-projection.json"
        projection = {
            "schema": "narada.operator_surfaces.operator_workspace_selector_projection.v0",
            "selectors": [
                {
                    "selector_id": "DISPLAY2",
                    "selector_scope": {
                        "kind": "monitor_context",
                        "monitor_surface_mode": "operator_surface",
                    },
                    "active_workspace_id": "narada-andrey",
                    "workspaces": [
                        {
                            "workspace_id": "narada-andrey",
                            "display_name": "Narada Andrey",
                            "surface_state": "running",
                            "member_count": 2,
                        }
                    ],
                    "launchable_workspaces": [
                        {
                            "workspace_id": "narada-utz",
                            "display_name": "Narada Utz",
                            "surface_state": "launchable",
                            "member_count": 0,
                        }
                    ],
                }
            ],
        }
        projection_path.write_text(json.dumps(projection), encoding="utf-8")

        full_workspaces = [
            {
                "workspace_id": "narada-andrey",
                "display_name": "Narada Andrey",
                "surface_state": "running",
                "members": [{}, {}],
            },
            {
                "workspace_id": "narada-utz",
                "display_name": "Narada Utz",
                "surface_state": "launchable",
                "members": [],
            },
        ]

        widget = _MockWidget(str(projection_path), full_workspaces)
        projected, active_id, signature = widget._selector_projection_for_screen(
            {}, full_workspaces
        )

        ids = [w["workspace_id"] for w in projected]
        assert "narada-andrey" in ids, "running workspace must be in projection"
        assert "narada-utz" in ids, "launchable workspace must be in projection"
        assert active_id == "narada-andrey", "active workspace id must be preserved"


def test_launchable_workspaces_are_split_correctly():
    with TemporaryDirectory() as tmp:
        projection_path = Path(tmp) / "selector-projection.json"
        projection = {
            "selectors": [
                {
                    "selector_id": "DISPLAY2",
                    "selector_scope": {"kind": "monitor_context"},
                    "active_workspace_id": "narada-andrey",
                    "workspaces": [
                        {
                            "workspace_id": "narada-andrey",
                            "display_name": "Narada Andrey",
                            "surface_state": "running",
                            "member_count": 2,
                        }
                    ],
                    "launchable_workspaces": [
                        {
                            "workspace_id": "narada-utz",
                            "display_name": "Narada Utz",
                            "surface_state": "launchable",
                            "member_count": 0,
                        }
                    ],
                }
            ],
        }
        projection_path.write_text(json.dumps(projection), encoding="utf-8")

        full_workspaces = [
            {
                "workspace_id": "narada-andrey",
                "display_name": "Narada Andrey",
                "surface_state": "running",
                "members": [{}, {}],
            },
            {
                "workspace_id": "narada-utz",
                "display_name": "Narada Utz",
                "surface_state": "launchable",
                "members": [],
            },
        ]

        widget = _MockWidget(str(projection_path), full_workspaces)
        projected, _, _ = widget._selector_projection_for_screen({}, full_workspaces)

        from core.widgets.yasb.operator_workspaces import _split_workspaces_by_activity

        live, launchable = _split_workspaces_by_activity(projected)
        live_ids = [w["workspace_id"] for w in live]
        launchable_ids = [w["workspace_id"] for w in launchable]

        assert live_ids == ["narada-andrey"], f"expected only running in live, got {live_ids}"
        assert launchable_ids == ["narada-utz"], f"expected only launchable in launchable, got {launchable_ids}"


if __name__ == "__main__":
    test_selector_projection_includes_launchable_workspaces()
    test_launchable_workspaces_are_split_correctly()
    print("operator workspace launchable selector tests passed")

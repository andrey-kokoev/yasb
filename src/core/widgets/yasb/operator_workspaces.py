import json
import logging
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QPushButton, QSizePolicy, QVBoxLayout

from core.utils.tooltip import set_tooltip
from core.utils.utilities import PopupWidget, refresh_widget_style
from core.validation.widgets.yasb.operator_workspaces import OperatorWorkspacesConfig
from core.widgets.base import BaseWidget


def _normalize_monitor_name(value: str | None) -> str:
    return str(value or "").replace("\\", "").replace(".", "").upper()


def _workspace_member_count(workspace: dict) -> int:
    member_count = workspace.get("member_count")
    if member_count is not None:
        try:
            return max(0, int(member_count))
        except (TypeError, ValueError):
            pass
    members = workspace.get("members") or []
    return len(members) if isinstance(members, list) else 0


def _workspace_surface_state(workspace: dict) -> str:
    state = str(
        workspace.get("surface_state")
        or workspace.get("embodiment_state")
        or workspace.get("lifecycle_state")
        or ""
    ).strip().lower()
    if state in {"running", "inhabited", "live"}:
        return "running"
    if state in {"launchable", "dormant", "inactive"}:
        return "launchable"
    if state in {"disabled", "unavailable", "absent"}:
        return "disabled"
    return ""


def _workspace_is_running(workspace: dict) -> bool:
    state = _workspace_surface_state(workspace)
    if state:
        return state == "running"
    return _workspace_member_count(workspace) > 0


def _split_workspaces_by_activity(workspaces: list[dict]) -> tuple[list[dict], list[dict]]:
    live_workspaces: list[dict] = []
    launchable_workspaces: list[dict] = []
    for workspace in workspaces:
        state = _workspace_surface_state(workspace)
        if state == "running":
            live_workspaces.append(workspace)
        elif state == "launchable":
            launchable_workspaces.append(workspace)
        elif _workspace_is_running(workspace):
            live_workspaces.append(workspace)
        else:
            launchable_workspaces.append(workspace)
    return live_workspaces, launchable_workspaces


def _monitor_scope_signature(workspace: dict) -> tuple:
    scope = workspace.get("monitor_scope") or {}
    return (
        str(scope.get("kind") or "all_monitors"),
        str(scope.get("monitor_role") or ""),
        str(scope.get("observed_monitor_name") or ""),
        str(scope.get("komorebi_monitor_index") or ""),
    )


def _monitor_scope_active_keys(scope: dict | None) -> list[str]:
    scope = scope or {}
    if str(scope.get("kind") or "all_monitors") != "single_monitor":
        return []

    keys = []
    observed_monitor_name = str(scope.get("observed_monitor_name") or "")
    if observed_monitor_name:
        keys.append(observed_monitor_name)

    monitor_role = str(scope.get("monitor_role") or "")
    if monitor_role:
        keys.append(monitor_role)

    komorebi_monitor_index = scope.get("komorebi_monitor_index")
    if komorebi_monitor_index is not None:
        keys.append(f"komorebi_monitor_index:{komorebi_monitor_index}")

    return list(dict.fromkeys(keys))


def _screen_matches_monitor_scope(
    scope: dict | None,
    screen_name: str | None,
    screen_role: str | None,
    left_to_right_index: int | None,
) -> bool:
    scope = scope or {}
    if str(scope.get("kind") or "all_monitors") != "single_monitor":
        return True

    observed_monitor_name = _normalize_monitor_name(scope.get("observed_monitor_name"))
    normalized_screen_name = _normalize_monitor_name(screen_name)
    if observed_monitor_name and normalized_screen_name and observed_monitor_name == normalized_screen_name:
        return True

    komorebi_monitor_index = scope.get("komorebi_monitor_index")
    if komorebi_monitor_index is not None and left_to_right_index is not None:
        try:
            return int(komorebi_monitor_index) == int(left_to_right_index)
        except (TypeError, ValueError):
            pass

    monitor_role = str(scope.get("monitor_role") or "")
    if monitor_role and screen_role:
        return monitor_role == screen_role

    return False


def _active_workspace_id_for_screen(
    workspaces: list[dict],
    global_active_workspace_id: str,
    active_workspace_by_monitor: dict | None,
    screen_name: str | None,
    screen_role: str | None,
    left_to_right_index: int | None,
) -> str:
    active_workspace_by_monitor = active_workspace_by_monitor or {}
    for workspace in workspaces:
        workspace_id = str(workspace.get("workspace_id") or "")
        if not workspace_id:
            continue
        if not _screen_matches_monitor_scope(
            workspace.get("monitor_scope"),
            screen_name,
            screen_role,
            left_to_right_index,
        ):
            continue
        for key in _monitor_scope_active_keys(workspace.get("monitor_scope")):
            if active_workspace_by_monitor.get(key) == workspace_id:
                return workspace_id

    return global_active_workspace_id


class OperatorWorkspaceButton(QPushButton):
    def __init__(self, workspace: dict, active: bool, parent: "OperatorWorkspacesWidget"):
        super().__init__(parent)
        self.parent_widget = parent
        self.workspace_id = str(workspace.get("workspace_id") or "")
        self.workspace = workspace
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.clicked.connect(self._on_clicked)
        self.update_from_workspace(workspace, active)

    def _on_clicked(self):
        self.parent_widget.activate_workspace(self.workspace_id)

    def update_from_workspace(self, workspace: dict, active: bool):
        self.workspace = workspace
        self.workspace_id = str(workspace.get("workspace_id") or "")
        display_name = str(workspace.get("display_name") or self.workspace_id)
        template = (
            self.parent_widget.config.label_workspace_active_btn
            if active
            else self.parent_widget.config.label_workspace_btn
        )
        text = template.format(
            workspace_id=self.workspace_id,
            display_name=display_name,
            member_count=_workspace_member_count(workspace),
        )
        max_len = self.parent_widget.config.label_max_length
        if max_len and len(text) > max_len:
            text = text[: max(1, max_len - 1)] + "..."
        self.setText(text)
        classes = ["ws-btn"]
        if active:
            classes.append("active")
        if _workspace_is_running(workspace):
            classes.append("populated")
        self.setProperty("class", " ".join(classes))
        if self.parent_widget.config.tooltip:
            set_tooltip(
                self,
                self.parent_widget.config.tooltip.format(
                    workspace_id=self.workspace_id,
                    display_name=display_name,
                    member_count=_workspace_member_count(workspace),
                ),
                delay=400,
                position="top",
            )
        refresh_widget_style(self)


class OperatorWorkspaceLaunchButton(QPushButton):
    def __init__(self, parent: "OperatorWorkspacesWidget"):
        super().__init__(parent)
        self.parent_widget = parent
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setProperty("class", "ws-btn launch-btn")
        self.setText(self.parent_widget.config.launch_button_label)
        self.clicked.connect(self._on_clicked)
        refresh_widget_style(self)

    def _on_clicked(self):
        self.parent_widget.toggle_launch_inventory()

    def update_state(self, has_launchable: bool):
        self.setVisible(has_launchable)
        if self.parent_widget.config.launch_button_tooltip:
            if has_launchable:
                tooltip = self.parent_widget.config.launch_button_tooltip.format(
                    dormant_count=len(self.parent_widget._launchable_workspaces)
                )
            else:
                tooltip = self.parent_widget.config.launch_button_tooltip_empty
            set_tooltip(self, tooltip, delay=400, position="top")
        refresh_widget_style(self)


class OperatorWorkspacesWidget(BaseWidget):
    validation_schema = OperatorWorkspacesConfig

    def __init__(self, config: OperatorWorkspacesConfig):
        super().__init__(config.update_interval, class_name="operator-workspaces")
        self.config = config
        self._buttons: dict[str, OperatorWorkspaceButton] = {}
        self._launch_button: OperatorWorkspaceLaunchButton | None = None
        self._launch_popup: PopupWidget | None = None
        self._launchable_workspaces: list[dict] = []
        self._last_signature: tuple | None = None
        self._init_container()
        self.callback_timer = "refresh_workspaces"
        self.register_callback("refresh_workspaces", self.refresh_workspaces)
        self.start_timer()

    def refresh_workspaces(self):
        try:
            state = self._load_json(self.config.workspace_state_path)
            workspaces = state.get("workspaces") or []
            projection = self._selector_projection_for_screen(state, workspaces)
            if projection is None:
                active_workspace_id, active_signature = self._active_workspace_selection(state, workspaces)
                projected_workspaces = [workspace for workspace in workspaces if self._workspace_matches_current_screen(workspace)]
            else:
                projected_workspaces, active_workspace_id, active_signature = projection

            workspace_ids = [str(workspace.get("workspace_id") or "") for workspace in workspaces]
            if active_workspace_id not in workspace_ids:
                active_workspace_id = str(state.get("active_workspace_id") or (workspace_ids[0] if workspace_ids else ""))
            live_workspaces, launchable_workspaces = _split_workspaces_by_activity(projected_workspaces)
            signature = (
                active_workspace_id,
                active_signature,
                self._screen_context_signature(),
                tuple(
                    (
                        str(workspace.get("workspace_id") or ""),
                        str(workspace.get("display_name") or ""),
                        _workspace_member_count(workspace),
                        _monitor_scope_signature(workspace),
                    )
                    for workspace in workspaces
                ),
                tuple(str(workspace.get("workspace_id") or "") for workspace in live_workspaces),
                tuple(str(workspace.get("workspace_id") or "") for workspace in launchable_workspaces),
            )
            if signature == self._last_signature:
                return
            self._last_signature = signature
            self._launchable_workspaces = launchable_workspaces
            self._sync_buttons(live_workspaces, active_workspace_id)
            self._sync_launch_button(bool(launchable_workspaces))
            self.setVisible(bool(live_workspaces) or bool(launchable_workspaces))
        except Exception:
            logging.exception("Failed to refresh Narada operator workspaces")
            self.setVisible(False)

    def activate_workspace(self, workspace_id: str):
        if not workspace_id:
            return
        try:
            screen_name, screen_role, left_to_right_index = self._screen_context_signature()
            args = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                self.config.switch_script_path,
                "-UserSiteRoot",
                self.config.user_site_root,
                "-PcSiteRoot",
                self.config.pc_site_root,
                "-WorkspaceId",
                workspace_id,
                "-Apply",
                "-MutatingAuthorized",
                self.config.mutating_authorized,
                "-PassThru",
            ]
            if screen_name:
                args.extend(["-SelectorMonitorName", screen_name])
            if screen_role:
                args.extend(["-SelectorMonitorRole", screen_role])
            if left_to_right_index is not None:
                args.extend(["-SelectorLeftToRightIndex", str(left_to_right_index)])

            subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            QTimer.singleShot(250, self.refresh_workspaces)
        except Exception:
            logging.exception("Failed to switch Narada operator workspace to %s", workspace_id)

    def toggle_launch_inventory(self):
        if self._launch_popup and self._launch_popup.isVisible():
            self._launch_popup.hide_animated()
            return
        self._show_launch_inventory()

    def _show_launch_inventory(self):
        if not self._launchable_workspaces:
            return
        popup = PopupWidget(
            self,
            blur=True,
            round_corners=True,
            round_corners_type="normal",
            border_color="System",
        )
        self._launch_popup = popup
        popup.setProperty("class", "operator-workspaces launch-menu")

        main_layout = QVBoxLayout(popup)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        for workspace in self._launchable_workspaces:
            workspace_id = str(workspace.get("workspace_id") or "")
            display_name = str(workspace.get("display_name") or workspace_id)
            item = QPushButton(f"{display_name} ({_workspace_member_count(workspace)})", popup)
            item.setProperty("class", "menu-item ws-btn launch-item")
            item.setCursor(Qt.CursorShape.PointingHandCursor)
            item.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            def handler(_checked=False, selected_id=workspace_id):
                self.activate_workspace(selected_id)
                if self._launch_popup and self._launch_popup.isVisible():
                    self._launch_popup.hide_animated()

            item.clicked.connect(handler)
            main_layout.addWidget(item)

        def on_popup_destroyed(*_args, popup_ref=popup):
            if self._launch_popup is popup_ref:
                self._launch_popup = None

        popup.destroyed.connect(on_popup_destroyed)
        popup.adjustSize()
        popup.setPosition(
            alignment="right",
            direction="down",
            offset_left=0,
            offset_top=6,
        )
        popup.show()

    def _active_workspace_selection(self, state: dict, workspaces: list[dict]) -> tuple[str, tuple]:
        runtime_path = self.config.runtime_state_path
        authority_active = str(state.get("active_workspace_id") or "")
        authority_map = state.get("active_workspace_by_monitor") or {}
        active = authority_active
        active_by_monitor = authority_map
        if runtime_path:
            try:
                runtime = self._load_json(runtime_path)
                authority_updated_at = str(state.get("updated_at") or "")
                runtime_updated_at = str(runtime.get("updated_at") or "")
                if authority_updated_at and runtime_updated_at and authority_updated_at > runtime_updated_at:
                    active = authority_active
                    active_by_monitor = authority_map
                else:
                    runtime_active = str(runtime.get("active_workspace_id") or "")
                    active = runtime_active or authority_active
                    active_by_monitor = runtime.get("active_workspace_by_monitor") or authority_map
            except Exception:
                pass

        screen_name, screen_role, left_to_right_index = self._screen_context_signature()
        active_for_screen = _active_workspace_id_for_screen(
            workspaces,
            active,
            active_by_monitor,
            screen_name,
            screen_role,
            left_to_right_index,
        )
        active_signature = (
            active,
            tuple(sorted((str(key), str(value)) for key, value in active_by_monitor.items())),
        )
        return active_for_screen, active_signature

    def _selector_projection_for_screen(self, state: dict, workspaces: list[dict]) -> tuple[list[dict], str, tuple] | None:
        path = self.config.selector_projection_path
        if not path:
            return None
        projection_path = Path(path)
        if not projection_path.exists():
            return None

        projection = self._load_json(str(projection_path))
        selectors = projection.get("selectors") or []
        screen_name, screen_role, left_to_right_index = self._screen_context_signature()
        selector = None
        for candidate in selectors:
            if _screen_matches_monitor_scope(
                candidate.get("selector_scope"),
                screen_name,
                screen_role,
                left_to_right_index,
            ):
                selector = candidate
                break
        if selector is None:
            return ([], "", ("selector_projection", str(projection.get("generated_at") or ""), "no_selector"))

        workspace_by_id = {str(workspace.get("workspace_id") or ""): workspace for workspace in workspaces}
        visible = []
        projected_ids = []
        for projected_workspace in selector.get("workspaces") or []:
            workspace_id = str(projected_workspace.get("workspace_id") or "")
            if not workspace_id:
                continue
            projected_ids.append(workspace_id)
            workspace = workspace_by_id.get(workspace_id)
            if workspace is not None:
                visible.append(workspace)

        active_workspace_id = str(selector.get("active_workspace_id") or "")
        active_signature = (
            "selector_projection",
            str(projection.get("generated_at") or ""),
            str(selector.get("selector_id") or ""),
            tuple(projected_ids),
            active_workspace_id,
        )
        return (visible, active_workspace_id, active_signature)

    def _sync_buttons(self, workspaces: list[dict], active_workspace_id: str):
        workspace_ids = [str(workspace.get("workspace_id") or "") for workspace in workspaces]
        for old_id in list(self._buttons.keys()):
            if old_id not in workspace_ids:
                button = self._buttons.pop(old_id)
                self._widget_container_layout.removeWidget(button)
                button.setParent(None)

        for workspace in workspaces:
            workspace_id = str(workspace.get("workspace_id") or "")
            if not workspace_id:
                continue
            active = workspace_id == active_workspace_id
            button = self._buttons.get(workspace_id)
            if button is None:
                button = OperatorWorkspaceButton(workspace, active, self)
                self._buttons[workspace_id] = button
                self._widget_container_layout.addWidget(button)
            else:
                button.update_from_workspace(workspace, active)

        self._renumber_visible_buttons()

    def _sync_launch_button(self, has_launchable: bool):
        if self._launch_button is None:
            self._launch_button = OperatorWorkspaceLaunchButton(self)
            self._widget_container_layout.addWidget(self._launch_button)
        self._launch_button.update_state(has_launchable)

    def _renumber_visible_buttons(self):
        ordered_buttons = list(self._buttons.values())
        if self._launch_button and self._launch_button.isVisible():
            ordered_buttons.append(self._launch_button)
        for index, button in enumerate(ordered_buttons, start=1):
            classes = [part for part in str(button.property("class") or "").split() if not part.startswith("button-")]
            classes.append(f"button-{index}")
            button.setProperty("class", " ".join(classes))
            refresh_widget_style(button)

    def _workspace_matches_current_screen(self, workspace: dict) -> bool:
        screen_name, screen_role, left_to_right_index = self._screen_context_signature()
        return _screen_matches_monitor_scope(
            workspace.get("monitor_scope"),
            screen_name,
            screen_role,
            left_to_right_index,
        )

    def _screen_context_signature(self) -> tuple[str, str | None, int | None]:
        screen = self._current_screen()
        if screen is None:
            return (str(self.screen_name or ""), None, None)

        return (
            str(self.screen_name or screen.name() or ""),
            self._screen_monitor_role(screen),
            self._screen_left_to_right_index(screen),
        )

    def _current_screen(self):
        for screen in QApplication.screens():
            if self.screen_name and screen.name() == self.screen_name:
                return screen
        return self.screen()

    def _screen_monitor_role(self, screen) -> str:
        primary = QApplication.primaryScreen()
        if primary is None or screen == primary:
            return "right_or_primary"
        if screen.geometry().center().x() < primary.geometry().center().x():
            return "left_or_secondary"
        return "right_or_primary"

    def _screen_left_to_right_index(self, screen) -> int | None:
        screens = sorted(QApplication.screens(), key=lambda item: item.geometry().center().x())
        for index, candidate in enumerate(screens):
            if candidate == screen:
                return index
        return None

    @staticmethod
    def _load_json(path: str) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))

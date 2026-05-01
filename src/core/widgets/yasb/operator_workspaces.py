import json
import logging
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QPushButton, QSizePolicy

from core.utils.tooltip import set_tooltip
from core.utils.utilities import refresh_widget_style
from core.validation.widgets.yasb.operator_workspaces import OperatorWorkspacesConfig
from core.widgets.base import BaseWidget


def _normalize_monitor_name(value: str | None) -> str:
    return str(value or "").replace("\\", "").replace(".", "").upper()


def _monitor_scope_signature(workspace: dict) -> tuple:
    scope = workspace.get("monitor_scope") or {}
    return (
        str(scope.get("kind") or "all_monitors"),
        str(scope.get("monitor_role") or ""),
        str(scope.get("observed_monitor_name") or ""),
        str(scope.get("komorebi_monitor_index") or ""),
    )


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
            member_count=len(workspace.get("members") or []),
        )
        max_len = self.parent_widget.config.label_max_length
        if max_len and len(text) > max_len:
            text = text[: max(1, max_len - 1)] + "..."
        self.setText(text)
        self.setProperty("class", "ws-btn active" if active else "ws-btn")
        if self.parent_widget.config.tooltip:
            set_tooltip(
                self,
                self.parent_widget.config.tooltip.format(
                    workspace_id=self.workspace_id,
                    display_name=display_name,
                    member_count=len(workspace.get("members") or []),
                ),
                delay=400,
                position="top",
            )
        refresh_widget_style(self)


class OperatorWorkspacesWidget(BaseWidget):
    validation_schema = OperatorWorkspacesConfig

    def __init__(self, config: OperatorWorkspacesConfig):
        super().__init__(config.update_interval, class_name="operator-workspaces")
        self.config = config
        self._buttons: dict[str, OperatorWorkspaceButton] = {}
        self._last_signature: tuple | None = None
        self._init_container()
        self.callback_timer = "refresh_workspaces"
        self.register_callback("refresh_workspaces", self.refresh_workspaces)
        self.start_timer()

    def refresh_workspaces(self):
        try:
            state = self._load_json(self.config.workspace_state_path)
            workspaces = state.get("workspaces") or []
            active_workspace_id = self._active_workspace_id(state)
            workspace_ids = [str(workspace.get("workspace_id") or "") for workspace in workspaces]
            if active_workspace_id not in workspace_ids:
                active_workspace_id = str(state.get("active_workspace_id") or (workspace_ids[0] if workspace_ids else ""))
            signature = (
                active_workspace_id,
                self._screen_context_signature(),
                tuple(
                    (
                        str(workspace.get("workspace_id") or ""),
                        str(workspace.get("display_name") or ""),
                        len(workspace.get("members") or []),
                        _monitor_scope_signature(workspace),
                    )
                    for workspace in workspaces
                ),
            )
            if signature == self._last_signature:
                return
            self._last_signature = signature
            self._sync_buttons(workspaces, active_workspace_id)
            self.setVisible(bool(workspaces))
        except Exception:
            logging.exception("Failed to refresh Narada operator workspaces")
            self.setVisible(False)

    def activate_workspace(self, workspace_id: str):
        if not workspace_id:
            return
        try:
            subprocess.Popen(
                [
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
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            QTimer.singleShot(250, self.refresh_workspaces)
        except Exception:
            logging.exception("Failed to switch Narada operator workspace to %s", workspace_id)

    def _active_workspace_id(self, state: dict) -> str:
        runtime_path = self.config.runtime_state_path
        authority_active = str(state.get("active_workspace_id") or "")
        if runtime_path:
            try:
                runtime = self._load_json(runtime_path)
                authority_updated_at = str(state.get("updated_at") or "")
                runtime_updated_at = str(runtime.get("updated_at") or "")
                if authority_updated_at and runtime_updated_at and authority_updated_at > runtime_updated_at:
                    return authority_active
                active = str(runtime.get("active_workspace_id") or "")
                if active:
                    return active
            except Exception:
                pass
        return authority_active

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
            active = workspace_id == active_workspace_id and self._workspace_matches_current_screen(workspace)
            button = self._buttons.get(workspace_id)
            if button is None:
                button = OperatorWorkspaceButton(workspace, active, self)
                self._buttons[workspace_id] = button
                self._widget_container_layout.addWidget(button)
            else:
                button.update_from_workspace(workspace, active)

        self._renumber_visible_buttons()

    def _renumber_visible_buttons(self):
        for index, button in enumerate(self._buttons.values(), start=1):
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

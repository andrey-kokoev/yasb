from core.validation.widgets.base_model import CustomBaseModel, KeybindingConfig


class OperatorWorkspacesConfig(CustomBaseModel):
    workspace_state_path: str
    runtime_state_path: str | None = None
    selector_projection_path: str | None = None
    switch_script_path: str
    user_site_root: str
    pc_site_root: str
    label_workspace_btn: str = "{display_name}"
    label_workspace_active_btn: str = "{display_name}"
    label_max_length: int = 18
    tooltip: str | None = "Narada operator workspace: {display_name}"
    update_interval: int = 1000
    mutating_authorized: str = "yasb.operator-workspace"
    keybindings: list[KeybindingConfig] = []

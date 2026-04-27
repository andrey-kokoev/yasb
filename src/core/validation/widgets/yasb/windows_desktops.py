from typing import Literal

from core.validation.widgets.base_model import (
    CallbacksConfig,
    CustomBaseModel,
    KeybindingConfig,
)


class WindowsDesktopsCallbacksConfig(CallbacksConfig):
    on_left: str = "activate_workspace"
    on_middle: str = "do_nothing"
    on_right: str = "toggle_context_menu"


class WindowsDesktopsMenuConfig(CustomBaseModel):
    blur: bool = True
    round_corners: bool = True
    round_corners_type: str = "normal"
    border_color: str = "System"
    alignment: Literal["left", "right", "center"] = "left"
    direction: Literal["up", "down"] = "down"
    offset_top: int = 6
    offset_left: int = 0
    show_window_count: bool = True


class WindowsDesktopsConfig(CustomBaseModel):
    render_mode: Literal["buttons", "current"] = "buttons"
    label_workspace_btn: str = "{index}"
    label_workspace_active_btn: str = "{index}"
    label_current_desktop: str = "{name}"
    tooltip: str | None = None
    menu: WindowsDesktopsMenuConfig = WindowsDesktopsMenuConfig()
    callbacks: WindowsDesktopsCallbacksConfig = WindowsDesktopsCallbacksConfig()
    keybindings: list[KeybindingConfig] = []

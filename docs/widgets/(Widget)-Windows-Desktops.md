# Windows Desktops Widget
| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `render_mode` | string | `'buttons'` | Render all desktop buttons (`buttons`) or only the current desktop label (`current`). |
| `label_workspace_btn` | string | `'{index}'` | The format string for workspace buttons. |
| `label_workspace_active_btn` | string | `'{index}'` | The format string for the active workspace button. |
| `label_current_desktop` | string | `'{name}'` | The format string used by `render_mode: 'current'`. |
| `menu` | dict | See below | Popup menu options for `render_mode: 'current'`. |
| `callbacks` | dict | `{'on_left': 'activate_workspace', 'on_middle': 'do_nothing', 'on_right': 'toggle_context_menu'}` | Callbacks for mouse events on workspace buttons. |

## Example Configuration

```yaml
windows_workspaces:
  type: "yasb.windows_desktops.WorkspaceWidget"
  options:
    label_workspace_btn: "\udb81\udc3d"
    label_workspace_active_btn: "\udb81\udc3e"
    callbacks:
      on_left: "activate_workspace"
      on_middle: "do_nothing"
      on_right: "toggle_context_menu"
```

### Current Desktop Mode

```yaml
windows_workspaces:
  type: "yasb.windows_desktops.WorkspaceWidget"
  options:
    render_mode: "current"
    label_current_desktop: "{name}"
    callbacks:
      on_left: "toggle_desktop_menu"
      on_middle: "do_nothing"
      on_right: "do_nothing"
    menu:
      blur: false
      round_corners: true
      alignment: "left"
      direction: "down"
      offset_top: 6
      show_window_count: true
```

## Description of Options
- **label_workspace_btn:** The format string for workspace buttons, can be icon, {index} or {name}.
- **label_workspace_active_btn:** The format string for the active workspace button, can be icon, {index} or {name}.
- **label_current_desktop:** The format string for current desktop mode, can use `{index}` or `{name}`.
- **menu:** Popup menu options for current desktop mode.
- **callbacks:** A dictionary specifying the callbacks for mouse events on workspace buttons. The keys are `on_left`, `on_middle`, and `on_right`, and the values are the names of the callback functions.

### Available Callbacks
| Callback               | Description                                                              |
|------------------------|--------------------------------------------------------------------------|
| `activate_workspace`   | Switch to the desktop associated with the clicked button.                |
| `toggle_context_menu`  | Show the right-click context menu options.                               |
| `toggle_desktop_menu`  | Show a popup menu of virtual desktops.                                   |
| `move_window_here`     | Move the currently focused window to the desktop of the clicked button.  |
| `delete_workspace`     | Delete the desktop associated with the clicked button.                   |
| `create_desktop`       | Create a new virtual desktop.                                            |
| `rename_desktop`       | Open a dialog to rename the desktop of the clicked button.               |
| `do_nothing`           | No action.                                                               |

## Style
```css
.windows-desktops {} /*Style for widget.*/
.windows-desktops .widget-container {} /*Style for widget container.*/
.windows-desktops .ws-btn {} /*Style for buttons.*/
.windows-desktops .ws-btn.active {} /*Style for the active workspace button.*/
.windows-desktops .current-desktop-label {} /*Style for the current desktop label.*/
.windows-workspaces .ws-btn.button-1 {} /*Style for first button.*/
.windows-workspaces .ws-btn.button-2 {} /*Style for second  button.*/
.windows-workspaces .ws-btn.active.button-1 {} /*Style for the active first workspace button.*/
.windows-workspaces .ws-btn.active.button-2 {} /*Style for the active second workspace button.*/

.windows-desktops-menu {} /*Style for current desktop popup menu.*/
.windows-desktops-menu .menu-item {} /*Style for popup menu item.*/
.windows-desktops-menu .menu-item:hover {} /*Style for hovered popup menu item.*/
.windows-desktops-menu .menu-item.active {} /*Style for active desktop menu item.*/
.windows-desktops-menu .menu-item-text {} /*Style for desktop name text.*/
.windows-desktops-menu .menu-item-count {} /*Style for desktop window count.*/

.windows-desktops .context-menu {} /*Style for context menu.*/
.windows-desktops .context-menu .menu-item {} /*Style for context menu items.*/
.windows-desktops .context-menu .menu-item:hover {} /*Style for selected context menu items.*/
.windows-desktops .context-menu .separator {} /*Style for context menu separator.*/

.windows-desktops .rename-dialog {} /*Style for rename dialog.*/
.windows-desktops .rename-dialog .popup-title {} /*Style for rename dialog title.*/
.windows-desktops .rename-dialog .popup-description {} /*Style for rename dialog description.*/
.windows-desktops .rename-dialog .rename-input {} /*Style for rename dialog input.*/
.windows-desktops .rename-dialog .button {} /*Style for rename dialog buttons.*/
.windows-desktops .rename-dialog .button.save {} /*Style for rename dialog save button.*/
.windows-desktops .rename-dialog .button.cancel {} /*Style for rename dialog cancel button. */
```

### Example
```css
.windows-desktops {
    padding: 0 4px 0 14px;
}
.windows-desktops .widget-container {
    background-color: #11111b;
    margin: 4px 0 4px 0;
    border-radius: 12px;
}
.windows-desktops .ws-btn {
    color: #7f849c;
    border: none;
    font-size: 14px;
    margin: 0 3px;
    padding: 0 
}
.windows-desktops .ws-btn.active {
    color: #89b4fa;
} 

.windows-desktops .context-menu {
    background-color:rgba(17, 17, 27, 0.75);
    border: none;
    border-radius: 2px;
    padding: 8px 0;
}
.windows-desktops .context-menu .menu-item {
    padding: 6px 16px;
}
.windows-desktops .context-menu .menu-item:hover {
    background-color: rgba(255,255,255,0.05);
    color: #ffffff;
}
.windows-desktops .context-menu .separator {
    margin: 2px 0px 2px 0px;
    height: 1px;
    background-color: rgba(255,255,255,0.1);
}


.windows-desktops-popup.rename {
    min-width: 320px;
    background-color: rgb(43, 43, 43);
}
.windows-desktops-popup.rename .windows-desktops-popup-container {
    padding: 16px;
}
.windows-desktops-popup.rename .windows-desktops-popup-footer {
    padding: 16px;
    background-color:rgb(32, 32, 32)
}
.windows-desktops-popup .popup-title {
    font-size: 16px;
    font-family: "Segoe UI Variable", "Segoe UI";
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 4px;
}
.windows-desktops-popup .popup-description {
    font-size: 13px;
    font-family: "Segoe UI Variable", "Segoe UI";
    font-weight: 400;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 12px;
}
.windows-desktops-popup .rename-input {
    font-size: 14px;
    font-family: "Segoe UI Variable", "Segoe UI";
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    background-color: rgba(255, 255, 255, 0.1);
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 8px;
    outline: none;
    min-width: 280px;
}
.windows-desktops-popup .rename-input:focus {
    border: 1px solid #4cc2ff;
}
.windows-desktops-popup .button {
    border-radius: 4px;
    font-family: "Segoe UI Variable", "Segoe UI";
    font-size: 13px;
    min-height: 28px;
    min-width: 120px;
    margin: 4px 0;
    background-color: rgb(43, 43, 43);
}
.windows-desktops-popup .button.save {
    margin-right: 8px;
}
.windows-desktops-popup .button:hover {
    background-color: rgba(255, 255, 255, 0.15);
}
```

> [!NOTE]  
> You can use `button-x` to style each button separately. Where x is the index of the button. Index starts from 1.

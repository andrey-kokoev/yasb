import logging
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.utils.alert_dialog import raise_info_alert
from core.utils.tooltip import set_tooltip
from core.utils.utilities import refresh_widget_style
from core.validation.widgets.yasb.whkd import WhkdConfig
from core.widgets.base import BaseWidget
from settings import SCRIPT_PATH


class KeybindsDialog(QDialog):
    def __init__(self, content, file_path, config: WhkdConfig, parent=None):
        super().__init__(parent)

        self.file_path = file_path
        self.original_content = content
        self.config = config
        self.special_keys = (
            {item.key: item.key_replace for item in self.config.special_keys} if self.config.special_keys else {}
        )
        self.setProperty("class", "whkd-popup")

        self.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        icon_path = os.path.join(SCRIPT_PATH, "assets", "images", "app_icon.png")
        icon = QIcon(icon_path)
        self.setWindowIcon(QIcon(icon.pixmap(48, 48)))

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)

        # Filter input
        self.filter_input = QLineEdit()
        self.filter_input.setProperty("class", "filter-input")
        self.filter_input.setPlaceholderText("Type to filter keybinds...")
        self.filter_input.setFixedHeight(28)
        self.filter_input.textChanged.connect(self.update_display)
        self.main_layout.addWidget(self.filter_input)

        # Scroll area for keybind rows
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("whkd_scroll_area")
        self.scroll_area.setStyleSheet("""
            QScrollArea#whkd_scroll_area {
                border: 0;
                background-color: transparent;
            }
            QScrollBar:vertical {
                width: 4px;
                margin: 0px;
                border: 0;
                background-color: transparent;
            }
            QScrollBar:vertical:hover {
                width: 0px;
                background-color: transparent;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255,255,255,0.2);
                min-height: 20px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(255,255,255,0.4);
            }
            QScrollBar::add-line:vertical {
                height: 0;
            }
            QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: 0;
                width: 0;
                height: 0;
                image: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.scroll_area.setWidgetResizable(True)

        self.main_layout.addWidget(self.scroll_area)

        self.container = QWidget()
        self.container.setObjectName("whkd_container_area")
        self.container.setStyleSheet("QWidget#whkd_container_area{background-color: transparent;border:none;}")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(2)
        self.scroll_area.setWidget(self.container)

        self.update_display()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)

    def show_near_anchor(self, anchor: QWidget):
        screen = QApplication.screenAt(anchor.mapToGlobal(anchor.rect().center())) or QApplication.primaryScreen()
        available = screen.availableGeometry()
        width = min(max(self.calculate_content_width(), 520), min(760, available.width() - 24))
        height = min(560, max(320, available.height() - 80))

        anchor_bottom = anchor.mapToGlobal(anchor.rect().bottomLeft())
        anchor_top = anchor.mapToGlobal(anchor.rect().topLeft())
        x = max(available.left() + 8, min(anchor_bottom.x(), available.right() - width - 8))
        y = anchor_bottom.y() + 8

        if y + height > available.bottom():
            y = anchor_top.y() - height - 8
        y = max(available.top() + 8, min(y, available.bottom() - height - 8))

        self.setGeometry(x, y, width, height)
        self.show()
        self.raise_()
        self.activateWindow()
        self.filter_input.setFocus()

    def calculate_content_width(self):
        min_width = 400
        # Inspect all keybind rows to find the widest one
        for i in range(self.container_layout.count()):
            item = self.container_layout.itemAt(i)
            if item and item.widget():
                # Get the sizeHint width of each row
                row_width = item.widget().sizeHint().width()
                min_width = max(min_width, row_width + 50)

                # If this is a keybind row with buttons and command, check their widths too
                if isinstance(item.widget(), QWidget) and hasattr(item.widget(), "layout"):
                    row_layout = item.widget().layout()
                    if row_layout:
                        width_sum = 0
                        for j in range(row_layout.count()):
                            child_item = row_layout.itemAt(j)
                            if child_item and child_item.widget():
                                width_sum += child_item.widget().sizeHint().width()
                        min_width = max(min_width, width_sum + 70)

        # Add margins to account for the dialog's layout
        margins = self.main_layout.contentsMargins()
        min_width += margins.left() + margins.right()

        # Cap the width at 80% of screen width
        screen_width = QApplication.primaryScreen().geometry().width()
        return min(min_width, int(screen_width * 0.8))

    def update_display(self):
        no_plus_modifiers = {key.lower() for key in self.special_keys.keys()}
        # Clear any existing content
        for i in reversed(range(self.container_layout.count())):
            self.widget = self.container_layout.itemAt(i).widget()
            if self.widget:
                self.widget.deleteLater()

        filter_text = self.filter_input.text().lower()
        for entry in self.original_content:
            keybind = entry.get("keybind")
            command = entry.get("display_command", entry.get("command"))
            if (
                filter_text
                and filter_text not in entry.get("search", "").lower()
            ):
                continue

            if keybind is None:
                # Render header
                self.header = QLabel(command)
                self.header.setProperty("class", "keybind-header")

                self.container_layout.addWidget(self.header)
            elif "group" in entry:
                self._render_grouped_row(entry)
            else:
                # Render keybind row
                self.row = QWidget()
                self.row.setProperty("class", "keybind-row")
                self.row_layout = QHBoxLayout(self.row)

                self.row_layout.setContentsMargins(5, 5, 5, 5)
                self.row_layout.setSpacing(0)
                self.row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

                # Create a container widget for buttons
                # Create a container widget for buttons
                buttons_container = QWidget(self.row)
                buttons_container.setProperty("class", "keybind-buttons-container")

                buttons_layout = QHBoxLayout(buttons_container)
                buttons_layout.setContentsMargins(0, 0, 0, 0)

                buttons_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

                def create_key_button(key_text):
                    btn = QPushButton(self._friendly_key_text(key_text.lower()))
                    if key_text.lower() in self.special_keys:
                        btn.setProperty("class", "keybind-button special")
                    else:
                        btn.setProperty("class", "keybind-button")
                    btn.setFixedHeight(28)
                    btn.setMinimumWidth(28)
                    btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                    buttons_layout.addWidget(btn)
                    refresh_widget_style(btn)
                    return btn

                if " + " in keybind:
                    groups = keybind.split(" + ")
                    for idx, group in enumerate(groups):
                        keys = group.split()
                        for key in keys:
                            create_key_button(key)

                        # Add plus button between groups if needed
                        if idx < len(groups) - 1:
                            next_keys = groups[idx + 1].split()
                            if not (
                                keys
                                and next_keys
                                and (
                                    keys[-1].lower() in no_plus_modifiers and next_keys[0].lower() in no_plus_modifiers
                                )
                            ):
                                plus_btn = QPushButton("+")
                                plus_btn.setEnabled(False)
                                plus_btn.setProperty("class", "plus-separator")
                                plus_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                                buttons_layout.addWidget(plus_btn)
                else:
                    keys = [k.strip() for k in keybind.split("+")]
                    for key in keys:
                        create_key_button(key)

                # Add the buttons container to the row
                self.row_layout.addWidget(buttons_container)

                # The command label
                self.command_label = QLabel(command)
                self.command_label.setProperty("class", "keybind-command")
                self.row_layout.addWidget(self.command_label)

                self.container_layout.addWidget(self.row)
                refresh_widget_style(self.row)

    def _render_grouped_row(self, entry):
        self.row = QWidget()
        self.row.setProperty("class", "keybind-row grouped")
        self.row_layout = QHBoxLayout(self.row)
        self.row_layout.setContentsMargins(4, 3, 4, 3)
        self.row_layout.setSpacing(0)
        self.row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        keys_container = QWidget(self.row)
        keys_container.setProperty("class", "keybind-buttons-container")
        keys_layout = QHBoxLayout(keys_container)
        keys_layout.setContentsMargins(0, 0, 0, 0)
        keys_layout.setSpacing(2)
        keys_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for key in entry.get("modifiers", []):
            btn = QPushButton(self._friendly_key_text(key.lower()))
            btn.setProperty("class", "keybind-button special")
            btn.setFixedHeight(22)
            btn.setMinimumWidth(26)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            keys_layout.addWidget(btn)
            refresh_widget_style(btn)

        for item in entry["group"]:
            key_text = self._friendly_key_text(item["key"].lower())
            label_text = item["label"]
            pill_text = key_text if key_text == label_text else f"{key_text} {label_text}"
            pill = QLabel(pill_text)
            pill.setProperty("class", "keybind-pill")
            keys_layout.addWidget(pill)
            refresh_widget_style(pill)

        self.row_layout.addWidget(keys_container)

        self.command_label = QLabel(entry.get("display_command", entry["command"]))
        self.command_label.setProperty("class", "keybind-command")
        self.row_layout.addWidget(self.command_label)

        self.container_layout.addWidget(self.row)
        refresh_widget_style(self.row)

    def _friendly_key_text(self, k: str) -> str:
        key = k.lower()
        return self.special_keys.get(key, key.upper())


class WhkdWidget(BaseWidget):
    validation_schema = WhkdConfig

    def __init__(self, config: WhkdConfig):
        super().__init__(class_name="whkd-widget")
        self.config = config
        self._popup_dialog = None

        # Construct container
        self._init_container()
        self.build_widget_label(self.config.label, None)
        if self.config.tooltip:
            set_tooltip(self, self.config.tooltip, delay=400, position="top")

        self.register_callback("open_popup", self._open_popup)
        self.callback_left = "open_popup"

    def _open_popup(self):
        if self._popup_dialog and self._popup_dialog.isVisible():
            self._popup_dialog.close()
            return

        # Determine config file location
        whkd_config_home = os.getenv("WHKD_CONFIG_HOME")
        file_path = (
            os.path.join(whkd_config_home, "whkdrc")
            if whkd_config_home
            else os.path.join(os.path.expanduser("~"), ".config", "whkdrc")
        )
        if not os.path.exists(file_path):
            logging.error("File not found: %s", file_path)
            raise_info_alert(
                title="Error",
                msg=f"The specified file does not exist\n{file_path}",
                informative_msg="Please make sure the file exists and try again.",
                rich_text=True,
            )
            return

        # Read and process the configuration file
        try:
            with open(file_path) as f:
                raw_lines = f.readlines()
        except Exception as e:
            logging.error("Error reading file: %s", e)
            return

        content = self._process_file(raw_lines)
        self._popup_dialog = KeybindsDialog(content, file_path, self.config, self)
        self._popup_dialog.destroyed.connect(lambda: setattr(self, "_popup_dialog", None))
        self._popup_dialog.show_near_anchor(self)

    def _process_file(self, lines):
        # Filter lines: keep headers and non-comment lines
        filtered_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("##"):
                filtered_lines.append(stripped)
            elif not (stripped.startswith("#") or stripped.startswith(".shell")):
                # Remove inline comments; only add non-empty lines
                line_no_comment = line.split("#")[0].strip()
                if line_no_comment:
                    filtered_lines.append(line_no_comment)

        # Format the filtered lines into display entries.
        formatted_lines = []
        for line in filtered_lines:
            # Check if line is a header
            if line.startswith("##"):
                header_text = line.lstrip("#").strip()
                formatted_lines.append({"keybind": None, "command": header_text, "search": header_text})
            elif ":" in line:
                keybind, command = line.split(":", 1)
                formatted_lines.append(
                    {
                        "keybind": keybind.strip(),
                        "command": command.strip(),
                        "display_command": self._display_command(command.strip()),
                        "search": f"{keybind.strip()} {command.strip()} {self._display_command(command.strip())}",
                    }
                )
        return self._group_display_entries(formatted_lines)

    def _group_display_entries(self, entries):
        grouped_entries = []
        index = 0
        while index < len(entries):
            entry = entries[index]
            group = self._collect_group(entries, index)
            if group:
                grouped_entries.append(group["entry"])
                index = group["next_index"]
                continue
            grouped_entries.append(entry)
            index += 1
        return grouped_entries

    def _collect_group(self, entries, start_index):
        first = entries[start_index]
        if first.get("keybind") is None:
            return None

        parsed = self._parse_groupable_entry(first)
        if not parsed:
            return None

        group = [parsed]
        index = start_index + 1
        while index < len(entries):
            parsed_next = self._parse_groupable_entry(entries[index])
            if not parsed_next or parsed_next["group_key"] != parsed["group_key"]:
                break
            group.append(parsed_next)
            index += 1

        if len(group) < 2:
            return None

        return {
            "entry": {
                "keybind": "group",
                "command": parsed["raw_command"],
                "display_command": parsed["display_command"],
                "modifiers": parsed["modifiers"],
                "group": [{"key": item["key"], "label": item["label"]} for item in group],
                "search": " ".join(
                    [parsed["display_command"]]
                    + [item["source"].get("search", "") for item in group]
                    + [item["label"] for item in group]
                ),
            },
            "next_index": index,
        }

    def _parse_groupable_entry(self, entry):
        keybind = entry.get("keybind")
        command = entry.get("command", "")
        if not keybind:
            return None

        keys = [part.strip().lower() for part in keybind.split("+")]
        if len(keys) < 2:
            return None

        trigger_key = keys[-1]
        modifiers = keys[:-1]
        if not modifiers:
            return None

        if command.startswith("komorebic focus "):
            direction = command.rsplit(" ", 1)[-1]
            if trigger_key in {"h", "j", "k", "l"} and direction in {"left", "down", "up", "right"}:
                return self._groupable(entry, modifiers, trigger_key, direction, "Focus", "komorebic focus")

        if command.startswith("komorebic move "):
            direction = command.rsplit(" ", 1)[-1]
            if trigger_key in {"h", "j", "k", "l"} and direction in {"left", "down", "up", "right"}:
                return self._groupable(entry, modifiers, trigger_key, direction, "Move", "komorebic move")

        if command.startswith("komorebic stack "):
            direction = command.rsplit(" ", 1)[-1]
            if trigger_key in {"h", "j", "k", "l"} and direction in {"left", "down", "up", "right"}:
                return self._groupable(entry, modifiers, trigger_key, direction, "Stack", "komorebic stack")

        if command.startswith("komorebic cycle-move-to-monitor "):
            target = command.rsplit(" ", 1)[-1]
            if trigger_key in {"h", "l"} and target in {"previous", "next"}:
                return self._groupable(entry, modifiers, trigger_key, target, "Move to monitor", "komorebic cycle-move-to-monitor")

        if command.startswith("komorebic focus-workspace "):
            workspace = str(int(command.rsplit(" ", 1)[-1]) + 1)
            if trigger_key == workspace:
                return self._groupable(entry, modifiers, trigger_key, workspace, "Focus workspace", "komorebic focus-workspace")

        if command.startswith("komorebic move-to-workspace "):
            workspace = str(int(command.rsplit(" ", 1)[-1]) + 1)
            if trigger_key == workspace:
                return self._groupable(entry, modifiers, trigger_key, workspace, "Move to workspace", "komorebic move-to-workspace")

        return None

    def _groupable(self, entry, modifiers, trigger_key, label, display_command, raw_command):
        return {
            "source": entry,
            "modifiers": modifiers,
            "key": trigger_key,
            "label": label,
            "display_command": display_command,
            "raw_command": raw_command,
            "group_key": (tuple(modifiers), raw_command),
        }

    def _display_command(self, command: str) -> str:
        if command.startswith("komorebic "):
            action = command.removeprefix("komorebic ")
            parts = action.split()
            if len(parts) == 2 and parts[0] in {"focus-workspace", "move-to-workspace"}:
                workspace = str(int(parts[1]) + 1)
                if parts[0] == "focus-workspace":
                    return f"Focus workspace {workspace}"
                return f"Move to workspace {workspace}"
            return " ".join(word.capitalize() for word in action.replace("-", " ").split())

        if "taskkill" in command and "whkd" in command.lower():
            return "Reload WHKD"

        return command

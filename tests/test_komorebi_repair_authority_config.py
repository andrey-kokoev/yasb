import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USER_SITE = Path("C:/Users/Andrey/Narada")
CONFIG = USER_SITE / "templates" / "pc-sites" / "windows-komorebi-yasb" / "tools" / "yasb" / "config.yaml"


def _load_config_text():
    return CONFIG.read_text(encoding="utf-8")


def test_komorebi_repair_calls_authority_not_direct_script():
    text = _load_config_text()
    repair_section = text.split("komorebi_repair:")[1].split("komorebi_repair_state:")[0]
    assert "Invoke-KomorebiRepairAuthority.ps1" in repair_section
    assert "Repair-Komorebi.ps1" not in repair_section
    assert "repair_komorebi_strong" in repair_section
    assert "live_mutating" in repair_section


def test_komorebi_repair_state_widget_exists():
    text = _load_config_text()
    assert "komorebi_repair_state:" in text
    state_section = text.split("komorebi_repair_state:")[1].split("komorebi_repair:")[0]
    assert "Get-KomorebiRepairStateLabel.ps1" in state_section
    assert "run_interval: 5000" in state_section


def test_komorebi_repair_state_is_in_right_bar():
    text = _load_config_text()
    # Find the widgets.right list under primary-bar
    widgets_section = text.split("widgets:")[1].split("voice_capture_state:")[0]
    right_list = widgets_section.split("right:")[1].split("center:")[0]
    assert "komorebi_repair_state" in right_list


if __name__ == "__main__":
    test_komorebi_repair_calls_authority_not_direct_script()
    test_komorebi_repair_state_widget_exists()
    test_komorebi_repair_state_is_in_right_bar()
    print("komorebi repair authority config tests passed")

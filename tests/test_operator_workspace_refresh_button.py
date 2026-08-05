import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SOURCE = ROOT / "src" / "core" / "widgets" / "yasb" / "operator_workspaces.py"


def _module():
    return ast.parse(SOURCE.read_text(encoding="utf-8"))


def _class(module, class_name: str):
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise AssertionError(f"missing class {class_name}")


def _method(class_node, method_name: str):
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            return node
    raise AssertionError(f"missing method {method_name}")


def _calls_name(method_node, name: str) -> bool:
    for child in ast.walk(method_node):
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
            if child.func.attr == name:
                return True
    return False


def _contains_text(method_node, text: str) -> bool:
    for child in ast.walk(method_node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str) and text in child.value:
            return True
    return False


def test_refresh_button_class_exists_and_routes_to_reapply():
    module = _module()
    refresh_class = _class(module, "OperatorWorkspaceRefreshButton")
    assert _calls_name(_method(refresh_class, "_on_clicked"), "refresh_workspace")
    assert _calls_name(_method(refresh_class, "update_from_workspace"), "setVisible")


def test_widget_reapply_workspace_calls_repair_authority():
    module = _module()
    widget_class = _class(module, "OperatorWorkspacesWidget")
    refresh_method = _method(widget_class, "refresh_workspace")
    assert _calls_name(refresh_method, "Popen")
    assert _contains_text(refresh_method, "Invoke-KomorebiRepairAuthority.ps1")
    assert _contains_text(refresh_method, "reconcile_operator_workspace")


def test_widget_reapply_workspace_does_not_call_old_repair_script():
    module = _module()
    widget_class = _class(module, "OperatorWorkspacesWidget")
    refresh_method = _method(widget_class, "refresh_workspace")
    assert not _contains_text(refresh_method, "Repair-OperatorSurfaceWindows.ps1")


if __name__ == "__main__":
    test_refresh_button_class_exists_and_routes_to_reapply()
    test_widget_reapply_workspace_calls_repair_authority()
    test_widget_reapply_workspace_does_not_call_old_repair_script()
    print("operator workspace refresh button tests passed")

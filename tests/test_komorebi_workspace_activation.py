import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = ROOT / "src" / "core" / "widgets" / "komorebi" / "workspaces.py"
CLIENT = ROOT / "src" / "core" / "widgets" / "services" / "komorebi" / "client.py"


def _module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _class(module: ast.Module, name: str) -> ast.ClassDef:
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise AssertionError(f"class {name} not found")


def _method(class_node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"method {class_node.name}.{name} not found")


def _calls_attribute(node: ast.AST, attribute: str) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == attribute:
            return True
    return False


def test_workspace_buttons_delegate_to_guarded_activation_path():
    module = _module(WORKSPACES)
    for class_name in ("WorkspaceButton", "WorkspaceButtonWithIcons"):
        method = _method(_class(module, class_name), "activate_workspace")
        assert _calls_attribute(method, "activate_workspace_button")


def test_guarded_activation_ensures_empty_workspace_then_focuses_synchronously():
    module = _module(WORKSPACES)
    method = _method(_class(module, "WorkspaceWidget"), "activate_workspace_button")
    assert _calls_attribute(method, "ensure_workspaces")
    assert _calls_attribute(method, "activate_workspace")
    assert "wait=True" in ast.unparse(method)


def test_komorebi_client_exposes_ensure_workspaces_command():
    module = _module(CLIENT)
    method = _method(_class(module, "KomorebiClient"), "ensure_workspaces")
    source = ast.unparse(method)
    assert "ensure-workspaces" in source


if __name__ == "__main__":
    test_workspace_buttons_delegate_to_guarded_activation_path()
    test_guarded_activation_ensures_empty_workspace_then_focuses_synchronously()
    test_komorebi_client_exposes_ensure_workspaces_command()
    print("komorebi workspace activation tests passed")

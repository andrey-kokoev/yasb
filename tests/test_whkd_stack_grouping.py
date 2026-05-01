import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WHKD_WIDGET = ROOT / "src" / "core" / "widgets" / "yasb" / "whkd.py"


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


def test_whkd_widget_groups_komorebi_stack_directions():
    method = _method(_class(_module(WHKD_WIDGET), "WhkdWidget"), "_parse_groupable_entry")
    source = ast.unparse(method)
    assert "komorebic stack " in source
    assert "'Stack'" in source
    assert "'komorebic stack'" in source


if __name__ == "__main__":
    test_whkd_widget_groups_komorebi_stack_directions()
    print("whkd stack grouping tests passed")

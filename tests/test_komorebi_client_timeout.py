import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "src" / "core" / "widgets" / "services" / "komorebi" / "client.py"
EVENT_LISTENER = ROOT / "src" / "core" / "widgets" / "services" / "komorebi" / "event_listener.py"


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


def test_komorebi_state_query_uses_bounded_direct_process():
    module = _module(CLIENT)
    query_source = ast.unparse(_method(_class(module, "KomorebiClient"), "query_state"))
    subscribe_source = ast.unparse(_method(_class(module, "KomorebiClient"), "wait_until_subscribed_to_pipe"))
    resolve_source = ast.unparse(_method(_class(module, "KomorebiClient"), "_resolve_komorebic_path"))

    assert "timeout_secs: float=2.0" in ast.unparse(_method(_class(module, "KomorebiClient"), "__init__"))
    assert "shell=False" in query_source
    assert "shell=False" in subscribe_source
    assert "scoop" in resolve_source
    assert "current" in resolve_source


def test_event_listener_queries_state_before_subscription():
    module = _module(EVENT_LISTENER)
    method_source = ast.unparse(_method(_class(module, "KomorebiEventListener"), "_wait_until_komorebi_online"))

    assert method_source.index("query_state") < method_source.index("wait_until_subscribed_to_pipe")
    assert method_source.index("wait_until_subscribed_to_pipe") < method_source.index("ConnectNamedPipe")
    assert method_source.count("query_state") == 2
    retry_assignments = [
        node
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "KOMOREBI_OFFLINE_RETRY_SECONDS" for target in node.targets)
    ]
    assert retry_assignments, "offline retry backoff constant not found"
    retry_values = ast.literal_eval(retry_assignments[0].value)
    assert retry_values == (15, 30, 60)
    assert "Retrying in 2 second" not in method_source
    assert "logging.debug" in method_source


if __name__ == "__main__":
    test_komorebi_state_query_uses_bounded_direct_process()
    test_event_listener_queries_state_before_subscription()
    print("komorebi client timeout tests passed")

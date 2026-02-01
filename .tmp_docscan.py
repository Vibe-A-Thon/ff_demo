import ast
from pathlib import Path

ROOT = Path(r"f:\\code\\vibecode\\ffd\\ff_demo")
TARGET_DIRS = [ROOT / "backend", ROOT / "tests"]
REPORT = ROOT / "docscan_report.txt"

EXCLUDES = {".venv", "__pycache__", ".git", "node_modules"}


def iter_py_files():
    for base in TARGET_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if any(part in EXCLUDES for part in path.parts):
                continue
            yield path


def has_google_docstring(docstring: str) -> bool:
    if not docstring:
        return False
    markers = ["Args:", "Returns:", "Raises:", "Yields:"]
    return any(m in docstring for m in markers)


def scan_file(path: Path):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    findings = []

    module_doc = ast.get_docstring(tree)
    if not module_doc:
        findings.append(("module", "<module>", "missing module docstring"))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            doc = ast.get_docstring(node)
            if not doc:
                findings.append((kind, name, "missing docstring"))
            else:
                if not has_google_docstring(doc):
                    findings.append((kind, name, "docstring not Google-style"))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                missing_params = []
                for arg in node.args.args + node.args.kwonlyargs:
                    if arg.arg in ("self", "cls"):
                        continue
                    if arg.annotation is None:
                        missing_params.append(arg.arg)
                if node.args.vararg and node.args.vararg.annotation is None:
                    missing_params.append("*" + node.args.vararg.arg)
                if node.args.kwarg and node.args.kwarg.annotation is None:
                    missing_params.append("**" + node.args.kwarg.arg)
                if missing_params:
                    findings.append(("function", name, f"missing param type hints: {', '.join(missing_params)}"))
                if node.returns is None:
                    findings.append(("function", name, "missing return type hint"))
    return findings


all_findings = []
for py in iter_py_files():
    file_findings = scan_file(py)
    if file_findings:
        rel = py.relative_to(ROOT)
        for kind, name, issue in file_findings:
            all_findings.append((str(rel), kind, name, issue))

lines = []
lines.append("Docstring/Type Hint Scan Report")
lines.append("=" * 40)
lines.append(f"Scanned dirs: {', '.join(str(p.relative_to(ROOT)) for p in TARGET_DIRS if p.exists())}")
lines.append(f"Total findings: {len(all_findings)}")
lines.append("")
for rel, kind, name, issue in all_findings:
    lines.append(f"{rel} :: {kind} {name} :: {issue}")

REPORT.write_text("\n".join(lines), encoding="utf-8")
print(REPORT)

"""Validate documentation links, coverage, and runnable examples in disposable projects."""

from __future__ import annotations

import ast
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def python_blocks(path: Path) -> list[str]:
    return re.findall(r"```python\n(.*?)\n```", path.read_text(), re.DOTALL)


def check_documents() -> None:
    documents = [*ROOT.glob("*.md"), *DOCS.glob("*.md")]
    for document in documents:
        content = document.read_text()
        prose = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        prose = re.sub(r"`[^`\n]*`", "", prose)
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", prose):
            if "://" in target or target.startswith(("mailto:", "#")):
                continue
            relative = unquote(target.split("#", 1)[0])
            if not (document.parent / relative).exists():
                raise AssertionError(f"Broken link in {document.name}: {target}")
        for index, block in enumerate(python_blocks(document)):
            compile(block, f"{document.name}:python-block-{index + 1}", "exec")

    configuration = (DOCS / "configuration.md").read_text()
    settings_tree = ast.parse((ROOT / "fapilot/conf/settings.py").read_text())
    for node in ast.walk(settings_tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id.isupper():
                assert f"`{node.target.id}`" in configuration, node.target.id

    from fapilot.architectures import ARCHITECTURES

    structure = (DOCS / "project-structure.md").read_text()
    for slug, folders in ARCHITECTURES.items():
        assert f"`{slug}`" in structure, slug
        for folder in folders:
            assert f"`{folder}/`" in structure, folder

    reference = (DOCS / "api-reference.md").read_text()
    for module in (ROOT / "fapilot").rglob("*.py"):
        for node in ast.parse(module.read_text()).body:
            if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                if not node.name.startswith("_"):
                    assert node.name in reference, f"Undocumented API: {node.name}"
    print(f"Validated links, Python syntax, and reference coverage in {len(documents)} documents")


def run(command: list[str], directory: Path) -> None:
    environment = os.environ.copy()
    environment["PATH"] = (
        str(Path(sys.executable).parent) + os.pathsep + environment.get("PATH", "")
    )
    # Do not inherit database URLs or app settings from the caller.
    for key in list(environment):
        if key.startswith(("DATABASE", "FAPILOT_", "INSTALLED_APPS", "MIDDLEWARE")):
            del environment[key]
    result = subprocess.run(
        command, cwd=directory, env=environment, capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise RuntimeError(f"Command failed: {command}\n{result.stdout}\n{result.stderr}")
    print(f"Passed: {' '.join(command)}")


def check_walkthrough(directory: Path) -> None:
    run([sys.executable, "-c", "from fapilot.cli import main; main()",
         "startproject", "demo", "--architecture", "layered"], directory)
    project = directory / "demo"
    run([sys.executable, "manage.py", "startapp", "products"], project)
    settings = project / "config/settings.py"
    settings.write_text(settings.read_text().replace(
        "INSTALLED_APPS = []", 'INSTALLED_APPS = ["apps.products.apps.ProductsConfig"]'
    ))
    blocks = python_blocks(DOCS / "getting-started.md")
    for filename, content in zip(["models.py", "schemas.py", "api.py"], blocks[1:], strict=True):
        (project / "apps/products" / filename).write_text(content + "\n")
    for index, block in enumerate(python_blocks(DOCS / "testing.md")):
        (project / "tests" / f"test_documented_{index}.py").write_text(block + "\n")
    run([sys.executable, "-m", "pytest", "-q"], project)

    settings.write_text(settings.read_text().replace("DEBUG = True", "DEBUG = False"))
    run(["aerich", "--app", "models", "init-db"], project)
    run(["aerich", "--app", "products", "init-db"], project)
    model_path = project / "apps/products/models.py"
    model_path.write_text(
        model_path.read_text() + '    description = fields.TextField(default="")\n'
    )
    run([sys.executable, "manage.py", "makemigrations", "--app", "products",
         "--name", "add_description"], project)
    run([sys.executable, "manage.py", "migrate", "--app", "products"], project)
    with sqlite3.connect(project / "db.sqlite3") as connection:
        columns = connection.execute("PRAGMA table_info(product)").fetchall()
        assert "description" in [column[1] for column in columns]
    for app_name in ["reports", "metrics"]:
        package = project / "apps" / app_name
        package.mkdir()
        (package / "__init__.py").write_text("")
        (package / "models.py").write_text(
            "from tortoise import fields, models\n\n"
            f"class {app_name.title()}(models.Model):\n"
            "    id = fields.IntField(primary_key=True)\n"
        )
    settings.write_text(settings.read_text() + (
        '\nDATABASES = {"analytics": "sqlite://analytics.sqlite3"}\n'
        'DATABASE_APPS = {"reporting": {"default_connection": "analytics", '
        '"models": ["apps.reports.models", "apps.metrics.models"]}}\n'
    ))
    run(["aerich", "--app", "reporting", "init-db"], project)
    report_path = project / "apps/reports/models.py"
    report_path.write_text(
        report_path.read_text() + '    title = fields.CharField(max_length=100, default="")\n'
    )
    run([sys.executable, "manage.py", "makemigrations", "--app", "reporting",
         "--name", "add_title"], project)
    run([sys.executable, "manage.py", "migrate", "--app", "reporting"], project)
    with sqlite3.connect(project / "analytics.sqlite3") as connection:
        columns = connection.execute("PRAGMA table_info(reports)").fetchall()
        assert "title" in [column[1] for column in columns]
    print("Validated CRUD tests and migrations on both default and analytics databases")


def main() -> None:
    check_documents()
    with tempfile.TemporaryDirectory(prefix="fapilot-docs-") as directory:
        check_walkthrough(Path(directory))


if __name__ == "__main__":
    main()

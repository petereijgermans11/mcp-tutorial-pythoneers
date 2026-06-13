from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("project")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SKIP_DIRS = {".venv", "node_modules", "__pycache__", ".git", ".mypy_cache", ".pytest_cache"}
MAX_FILES = 200


def _iter_project_files():
    for path in PROJECT_ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            yield path.relative_to(PROJECT_ROOT).as_posix()


@mcp.tool()
def list_files() -> dict:
    """
    Geeft een lijst van bestanden in het project (max 200, zonder .venv/node_modules).
    """
    files = sorted(_iter_project_files())
    truncated = len(files) > MAX_FILES
    return {
        "files": files[:MAX_FILES],
        "total": len(files),
        "truncated": truncated,
    }


@mcp.tool()
def project_stats() -> dict:
    """
    Geeft basisstatistieken van het project.
    """
    files = list(_iter_project_files())
    python_files = [f for f in files if f.endswith(".py")]

    return {
        "total_files": len(files),
        "python_files": len(python_files),
    }


@mcp.tool()
def summarize_structure() -> str:
    """
    Geeft een globale samenvatting van de projectstructuur.
    """
    top_level = [p.name for p in PROJECT_ROOT.iterdir()]

    summary = (
        "Het project bevat de volgende hoofdonderdelen:\n"
        + "\n".join(f"- {name}" for name in top_level)
    )
    return summary


@mcp.tool()
def detect_risks() -> list[str]:
    """
    Simpele heuristiek om mogelijke risico's te signaleren.
    """
    risks = []

    if not (PROJECT_ROOT / "README.md").exists():
        risks.append("Geen README.md gevonden")

    if not any(
        p.is_dir() and p.name == "tests"
        for p in PROJECT_ROOT.iterdir()
        if p.name not in SKIP_DIRS
    ):
        risks.append("Geen testmap gevonden")

    large_files = [
        path for path in _iter_project_files()
        if path.endswith(".py")
        and (PROJECT_ROOT / path).stat().st_size > 3000
    ]
    if large_files:
        risks.append(f"Grote Python bestanden: {', '.join(large_files)}")

    return risks


if __name__ == "__main__":
    mcp.run(transport="stdio")

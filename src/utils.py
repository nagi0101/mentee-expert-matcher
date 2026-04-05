from __future__ import annotations

from pathlib import Path
import sys


GROUP_THEME = {
    "A": {"accent": "#2563eb", "soft": "#dbeafe", "ink": "#1d4ed8"},
    "B": {"accent": "#15803d", "soft": "#dcfce7", "ink": "#166534"},
    "C": {"accent": "#c2410c", "soft": "#ffedd5", "ink": "#9a3412"},
    "D": {"accent": "#7e22ce", "soft": "#f3e8ff", "ink": "#6b21a8"},
}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_cli_path(raw_path: Path, base_dir: Path) -> Path:
    return raw_path if raw_path.is_absolute() else (base_dir / raw_path).resolve()


def theme_class(group: str) -> str:
    return f"group-{group}"


def group_label(group: str) -> str:
    return f"코호트 {group}"


def warn(message: str) -> None:
    print(f"[WARN] {message}", file=sys.stderr)


def info(message: str) -> None:
    print(message)

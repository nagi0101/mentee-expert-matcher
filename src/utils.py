from __future__ import annotations

from pathlib import Path
import sys


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

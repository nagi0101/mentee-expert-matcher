from __future__ import annotations

import contextlib
from dataclasses import dataclass
import io
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
    try:
        from weasyprint import HTML
    except Exception as exc:  # pragma: no cover - import behavior depends on local environment
        HTML = None
        WEASYPRINT_IMPORT_ERROR = exc
    else:
        WEASYPRINT_IMPORT_ERROR = None


@dataclass
class RenderResult:
    html_path: Path
    pdf_path: Path
    pdf_generated: bool
    pdf_engine: str | None = None
    warning: str | None = None


def render_document(
    template_name: str,
    output_stem: str,
    context: dict[str, Any],
    templates_dir: Path,
    output_dir: Path,
    base_dir: Path,
) -> RenderResult:
    environment = build_environment(templates_dir)
    html = environment.get_template(template_name).render(**context)

    html_path = output_dir / f"{output_stem}.html"
    pdf_path = output_dir / f"{output_stem}.pdf"
    html_path.write_text(html, encoding="utf-8")

    try:
        engine = generate_pdf(html_path, pdf_path, base_dir)
        return RenderResult(
            html_path=html_path,
            pdf_path=pdf_path,
            pdf_generated=True,
            pdf_engine=engine,
        )
    except Exception as exc:
        if pdf_path.exists():
            pdf_path.unlink()
        return RenderResult(
            html_path=html_path,
            pdf_path=pdf_path,
            pdf_generated=False,
            warning=str(exc),
        )


def build_environment(templates_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def generate_pdf(html_path: Path, pdf_path: Path, _base_dir: Path) -> str:
    errors: list[str] = []

    if HTML is not None:
        try:
            HTML(filename=str(html_path), base_url=str(html_path.parent)).write_pdf(str(pdf_path))
            return "weasyprint"
        except Exception as exc:  # pragma: no cover - depends on local runtime
            errors.append(f"WeasyPrint 실패: {exc}")
    elif WEASYPRINT_IMPORT_ERROR is not None:
        errors.append(f"WeasyPrint import 실패: {WEASYPRINT_IMPORT_ERROR}")

    browser = find_browser()
    if browser is not None:
        try:
            run_browser_pdf(browser, html_path, pdf_path)
            return f"browser:{browser.stem}"
        except Exception as exc:  # pragma: no cover - depends on local runtime
            errors.append(f"{browser.name} 헤드리스 인쇄 실패: {exc}")
    else:
        errors.append("Microsoft Edge 또는 Google Chrome 실행 파일을 찾지 못했습니다.")

    raise RuntimeError(" / ".join(errors))


def find_browser() -> Path | None:
    candidates: list[Path] = []

    for raw_base in (
        os.environ.get("PROGRAMFILES"),
        os.environ.get("PROGRAMFILES(X86)"),
        os.environ.get("LOCALAPPDATA"),
    ):
        if not raw_base:
            continue
        base = Path(raw_base)
        candidates.extend(
            [
                base / "Microsoft" / "Edge" / "Application" / "msedge.exe",
                base / "Google" / "Chrome" / "Application" / "chrome.exe",
            ]
        )

    for executable in (
        "msedge",
        "chrome",
        "chromium",
        "google-chrome",
        "microsoft-edge",
    ):
        resolved = shutil.which(executable)
        if resolved:
            candidates.append(Path(resolved))

    candidates.extend(
        [
            Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
    )

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            return resolved
    return None


def run_browser_pdf(browser_path: Path, html_path: Path, pdf_path: Path) -> None:
    command = [
        str(browser_path),
        "--headless",
        "--disable-gpu",
        "--allow-file-access-from-files",
        f"--print-to-pdf={pdf_path}",
        "--no-pdf-header-footer",
        html_path.resolve().as_uri(),
    ]
    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=90,
    )

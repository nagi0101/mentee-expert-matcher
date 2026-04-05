from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


if __package__ in (None, ""):
    current_file = Path(__file__).resolve()
    current_root = current_file.parents[1]
    if str(current_root) not in sys.path:
        sys.path.insert(0, str(current_root))

from src.load_data import load_experts, load_trainees
from src.render import RenderResult, render_document
from src.schedule import (
    build_expert_badges,
    build_host_matrix,
    build_host_rounds,
    build_table_signs,
    build_trainee_badges,
    validate_schedule_integrity,
)
from src.utils import ensure_directory, info, project_root, resolve_cli_path, warn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="연수생/엑스퍼트 CSV를 바탕으로 이벤트 운영용 인쇄물을 생성합니다."
    )
    parser.add_argument("--trainees", required=True, type=Path, help="연수생 CSV 경로")
    parser.add_argument("--experts", required=True, type=Path, help="엑스퍼트 CSV 경로")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="산출물 저장 디렉터리 (기본값: output)",
    )
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        root = project_root()

        trainee_path = resolve_cli_path(args.trainees, root)
        expert_path = resolve_cli_path(args.experts, root)
        output_dir = ensure_directory(resolve_cli_path(args.output_dir, root))
        templates_dir = root / "templates"

        trainees = load_trainees(trainee_path)
        experts = load_experts(expert_path)

        trainee_badges = build_trainee_badges(trainees)
        expert_badges = build_expert_badges(experts)
        host_rounds = build_host_rounds(trainees, experts)
        host_matrix = build_host_matrix(host_rounds)
        table_signs = build_table_signs(experts)
        validate_schedule_integrity(trainees, host_rounds)

        stylesheet_href = Path(
            os.path.relpath(root / "assets" / "styles.css", output_dir)
        ).as_posix()
        documents = [
            {
                "template": "trainee_badges.html.j2",
                "stem": "trainee_badges",
                "context": {
                    "page_title": "연수생 이름표",
                    "badges": trainee_badges,
                    "stylesheet_href": stylesheet_href,
                },
            },
            {
                "template": "expert_badges.html.j2",
                "stem": "expert_badges",
                "context": {
                    "page_title": "엑스퍼트 이름표",
                    "badges": expert_badges,
                    "stylesheet_href": stylesheet_href,
                },
            },
            {
                "template": "host_schedule.html.j2",
                "stem": "host_schedule",
                "context": {
                    "page_title": "사회자용 전체 운영표",
                    "host_matrix": host_matrix,
                    "stylesheet_href": stylesheet_href,
                },
            },
            {
                "template": "table_signs.html.j2",
                "stem": "table_signs",
                "context": {
                    "page_title": "테이블 표지",
                    "signs": table_signs,
                    "stylesheet_href": stylesheet_href,
                },
            },
        ]

        results: list[RenderResult] = []
        for document in documents:
            results.append(
                render_document(
                    template_name=document["template"],
                    output_stem=document["stem"],
                    context=document["context"],
                    templates_dir=templates_dir,
                    output_dir=output_dir,
                    base_dir=root,
                )
            )

        info("생성 완료:")
        for result in results:
            info(f"- HTML: {result.html_path}")
            if result.pdf_generated:
                info(f"  PDF : {result.pdf_path} ({result.pdf_engine})")
            else:
                warn(f"{result.pdf_path.name} 생성 실패: {result.warning}")

        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

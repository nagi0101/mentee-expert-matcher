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

from src.config import build_config
from src.load_data import assign_groups, load_experts, load_trainees
from src.render import RenderResult, render_document
from src.schedule import (
    build_all_rounds,
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
    parser.add_argument("--tables", required=True, type=int, help="총 테이블 수")
    parser.add_argument("--trainees-per-table", required=True, type=int, help="테이블당 연수생 수 (최대)")
    parser.add_argument("--experts-per-table", type=int, default=2, help="테이블당 엑스퍼트 수 (기본값: 2)")
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

        # Load raw data
        raw_trainees = load_trainees(trainee_path)

        # Build config
        config = build_config(
            num_trainees=len(raw_trainees),
            num_tables=args.tables,
            trainees_per_table=args.trainees_per_table,
            experts_per_table=args.experts_per_table,
        )

        info(f"설정: 연수생 {config.num_trainees}명, 테이블 {config.num_tables}개, "
             f"테이블당 {config.trainees_per_table}명, {config.num_rounds}라운드, "
             f"{config.num_groups}그룹")
        if config.num_phantoms > 0:
            info(f"유령 회원 {config.num_phantoms}명 추가 (일부 테이블에 빈자리 발생)")

        # Assign groups and add phantoms
        trainees = assign_groups(raw_trainees, config)
        experts = load_experts(expert_path, config)

        # Build schedule
        all_rounds = build_all_rounds(config)
        trainee_badges = build_trainee_badges(trainees, all_rounds, config)
        expert_badges = build_expert_badges(experts)
        host_rounds = build_host_rounds(trainees, experts, all_rounds, config)
        host_matrix = build_host_matrix(host_rounds, config)
        table_signs = build_table_signs(experts, config)
        validate_schedule_integrity(trainees, host_rounds, config)

        # Dynamic CSS for group themes
        group_style_css = _build_group_css(config)

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
                    "group_style_css": group_style_css,
                    "num_groups": config.num_groups,
                    "num_rounds": config.num_rounds,
                    "badges_per_page": 6,
                },
            },
            {
                "template": "expert_badges.html.j2",
                "stem": "expert_badges",
                "context": {
                    "page_title": "엑스퍼트 이름표",
                    "badges": expert_badges,
                    "stylesheet_href": stylesheet_href,
                    "group_style_css": group_style_css,
                    "badges_per_page": 12,
                },
            },
            {
                "template": "host_schedule.html.j2",
                "stem": "host_schedule",
                "context": {
                    "page_title": "사회자용 전체 운영표",
                    "host_matrix": host_matrix,
                    "stylesheet_href": stylesheet_href,
                    "group_style_css": group_style_css,
                    "group_labels": config.group_labels,
                    "group_themes": config.group_themes,
                    "num_rounds": config.num_rounds,
                    "num_tables": config.num_tables,
                },
            },
            {
                "template": "table_signs.html.j2",
                "stem": "table_signs",
                "context": {
                    "page_title": "테이블 표지",
                    "signs": table_signs,
                    "stylesheet_href": stylesheet_href,
                    "group_style_css": group_style_css,
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


def _build_group_css(config) -> str:
    lines = [":root {"]
    for label, theme in config.group_themes.items():
        lower = label.lower()
        lines.append(f"  --{lower}: {theme['accent']};")
        lines.append(f"  --{lower}-soft: {theme['soft']};")
        lines.append(f"  --{lower}-ink: {theme['ink']};")
    lines.append("}")

    for label, theme in config.group_themes.items():
        cls = f"group-{label}"
        lines.append(f".trainee-badge.{cls} {{ --accent: {theme['accent']}; --ink: {theme['ink']}; background: #ffffff; }}")
        lines.append(f".trainee-badge.{cls} .badge-code {{ background: {theme['soft']}; color: {theme['ink']}; }}")
        lines.append(f".host-trainee.{cls} {{ color: {theme['ink']}; }}")
        lines.append(f".host-code.{cls} {{ background: {theme['soft']}; color: {theme['ink']}; border: 1px solid {theme['accent']}; }}")

    # Dynamic grid layout for host board
    lines.append(f".host-board {{ grid-template-columns: 28mm repeat({config.num_rounds}, minmax(0, 1fr)); "
                 f"grid-template-rows: 11mm repeat({config.num_tables}, minmax(0, 1fr)); }}")

    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from collections import defaultdict

from src.config import ScheduleConfig
from src.interests import summarize_org
from src.load_data import Expert, Trainee
from src.solutions import SCHEDULES
from src.utils import theme_class


def build_all_rounds(config: ScheduleConfig) -> list[list[list[int]]]:
    """Look up pre-computed schedule. Every trainee visits every table exactly once."""
    key = (config.num_tables, config.trainees_per_table)
    if key not in SCHEDULES:
        supported = sorted(SCHEDULES.keys())
        raise ValueError(
            f"({config.num_tables}, {config.trainees_per_table}) 조합은 "
            f"사전 계산된 스케줄이 없습니다. "
            f"지원 조합: {supported}"
        )
    return SCHEDULES[key]


def build_route(trainee_idx: int, all_rounds: list[list[list[int]]], config: ScheduleConfig) -> list[int]:
    """Get the table sequence (1-based) for a trainee across all rounds."""
    route = []
    for round_tables in all_rounds:
        for table_num, table in enumerate(round_tables):
            if trainee_idx in table:
                route.append(table_num + 1)  # 1-based
                break
    return route


def build_trainee_badges(
    trainees: list[Trainee],
    all_rounds: list[list[list[int]]],
    config: ScheduleConfig,
) -> list[dict[str, object]]:
    badges: list[dict[str, object]] = []
    for idx, trainee in enumerate(trainees):
        if trainee.is_phantom:
            continue
        route = build_route(idx, all_rounds, config)
        badges.append(
            {
                "name": trainee.name,
                "code": trainee.code,
                "theme_class": theme_class(trainee.group),
                "route": [
                    {"round": round_no, "table": table}
                    for round_no, table in enumerate(route, start=1)
                ],
                **summarize_org(trainee.org, layout_name="trainee"),
            }
        )
    return badges


def build_expert_badges(experts: list[Expert]) -> list[dict[str, object]]:
    badges: list[dict[str, object]] = []
    for expert in experts:
        if expert.is_placeholder:
            continue
        badges.append(
            {
                "name": expert.name,
                "table": expert.table,
                **summarize_org(expert.org, layout_name="expert"),
            }
        )
    return badges


def build_host_rounds(
    trainees: list[Trainee],
    experts: list[Expert],
    all_rounds: list[list[list[int]]],
    config: ScheduleConfig,
) -> list[dict[str, object]]:
    experts_by_table = build_experts_by_table(experts, config)

    rounds: list[dict[str, object]] = []
    for round_no, round_tables in enumerate(all_rounds, start=1):
        tables: list[dict[str, object]] = []
        for table_num in range(config.num_tables):
            table_indices = round_tables[table_num]
            trainees_for_table = []
            for idx in sorted(table_indices):
                t = trainees[idx]
                if t.is_phantom:
                    continue
                trainees_for_table.append(
                    {
                        "name": t.name,
                        "code": t.code,
                        "theme_class": theme_class(t.group),
                    }
                )
            trainees_for_table.sort(key=lambda item: (item["code"], item["name"]))

            table_key = table_num + 1
            experts_for_table = [
                e for e in experts_by_table[table_key] if not e.is_placeholder
            ]
            tables.append(
                {
                    "table_number": table_key,
                    "experts": [{"name": e.name} for e in experts_for_table],
                    "expert_names": " / ".join(e.name for e in experts_for_table) or "미배정",
                    "has_experts": bool(experts_for_table),
                    "trainees": trainees_for_table,
                }
            )
        rounds.append({"round_number": round_no, "tables": tables})

    return rounds


def build_host_matrix(
    rounds: list[dict[str, object]],
    config: ScheduleConfig,
) -> dict[str, object]:
    table_rows: list[dict[str, object]] = []
    round_numbers = [round_info["round_number"] for round_info in rounds]

    for table in range(1, config.num_tables + 1):
        anchor_table_info = next(
            item for item in rounds[0]["tables"] if item["table_number"] == table
        )
        cells: list[dict[str, object]] = []
        for round_info in rounds:
            table_info = next(
                item for item in round_info["tables"] if item["table_number"] == table
            )
            cells.append(
                {
                    "round_number": round_info["round_number"],
                    "experts": table_info["experts"],
                    "expert_names": table_info["expert_names"],
                    "has_experts": table_info["has_experts"],
                    "trainees": table_info["trainees"],
                }
            )
        table_rows.append(
            {
                "table_number": table,
                "experts": anchor_table_info["experts"],
                "expert_names": anchor_table_info["expert_names"],
                "has_experts": anchor_table_info["has_experts"],
                "cells": cells,
            }
        )

    return {"round_numbers": round_numbers, "table_rows": table_rows}


def build_table_signs(
    experts: list[Expert],
    config: ScheduleConfig,
) -> list[dict[str, object]]:
    experts_by_table = build_experts_by_table(experts, config)
    signs: list[dict[str, object]] = []
    for table in range(1, config.num_tables + 1):
        sign_experts = [
            {
                "name": expert.name,
                "org": expert.org,
                "has_org": bool(expert.org),
                "is_empty": expert.is_placeholder,
            }
            for expert in experts_by_table[table]
        ]
        signs.append(
            {
                "table": table,
                "experts": sign_experts,
                "has_slots": bool(sign_experts),
            }
        )
    return signs


def validate_schedule_integrity(
    trainees: list[Trainee],
    rounds: list[dict[str, object]],
    config: ScheduleConfig,
) -> None:
    real_codes = sorted(t.code for t in trainees if not t.is_phantom)

    for round_info in rounds:
        round_number = int(round_info["round_number"])
        round_codes: list[str] = []
        for table_info in round_info["tables"]:
            round_codes.extend(item["code"] for item in table_info["trainees"])

        if sorted(round_codes) != real_codes:
            raise ValueError(
                f"라운드 {round_number}의 전체 배치가 잘못되었습니다. "
                f"연수생 누락 또는 중복이 있습니다."
            )


def build_experts_by_table(
    experts: list[Expert],
    config: ScheduleConfig,
) -> dict[int, list[Expert]]:
    experts_by_table: dict[int, list[Expert]] = defaultdict(list)
    for expert in experts:
        experts_by_table[expert.table].append(expert)

    normalized: dict[int, list[Expert]] = {}
    for table in range(1, config.num_tables + 1):
        normalized[table] = sorted(
            experts_by_table[table],
            key=lambda item: (item.pair_order, item.name),
        )
    return normalized

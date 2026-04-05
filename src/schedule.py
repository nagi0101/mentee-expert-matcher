from __future__ import annotations

from collections import defaultdict

from src.interests import summarize_org
from src.load_data import Expert, Trainee
from src.utils import theme_class


SCHEDULE_RULES = {
    "A": (1, 2, 3, 4, 5, 0),
    "B": (0, 4, 5, 1, 2, 3),
    "C": (1, 0, 4, 2, 5, 3),
    "D": (2, 3, 0, 4, 5, 1),
}


def build_route(trainee: Trainee) -> list[int]:
    offsets = SCHEDULE_RULES[trainee.group]
    return [wrap_table(trainee.number + offset) for offset in offsets]


def build_trainee_badges(trainees: list[Trainee]) -> list[dict[str, object]]:
    badges: list[dict[str, object]] = []
    for trainee in trainees:
        badges.append(
            {
                "name": trainee.name,
                "code": trainee.code,
                "theme_class": theme_class(trainee.group),
                "route": [
                    {"round": round_no, "table": table}
                    for round_no, table in enumerate(build_route(trainee), start=1)
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


def build_host_rounds(trainees: list[Trainee], experts: list[Expert]) -> list[dict[str, object]]:
    experts_by_table = build_experts_by_table(experts)
    round_assignments: dict[int, dict[int, list[dict[str, str]]]] = {
        round_no: {table: [] for table in range(1, 7)} for round_no in range(1, 7)
    }

    for trainee in trainees:
        route = build_route(trainee)
        for round_no, table in enumerate(route, start=1):
            round_assignments[round_no][table].append(
                {
                    "name": trainee.name,
                    "code": trainee.code,
                    "theme_class": theme_class(trainee.group),
                }
            )

    rounds: list[dict[str, object]] = []
    for round_no in range(1, 7):
        tables: list[dict[str, object]] = []
        for table in range(1, 7):
            trainees_for_table = sorted(
                round_assignments[round_no][table],
                key=lambda item: (item["code"], item["name"]),
            )
            experts_for_table = [
                expert for expert in experts_by_table[table] if not expert.is_placeholder
            ]
            tables.append(
                {
                    "table_number": table,
                    "experts": [
                        {
                            "name": expert.name,
                        }
                        for expert in experts_for_table
                    ],
                    "expert_names": " / ".join(expert.name for expert in experts_for_table)
                    or "미배정",
                    "has_experts": bool(experts_for_table),
                    "trainees": trainees_for_table,
                }
            )
        rounds.append({"round_number": round_no, "tables": tables})

    return rounds


def build_host_matrix(rounds: list[dict[str, object]]) -> dict[str, object]:
    table_rows: list[dict[str, object]] = []
    round_numbers = [round_info["round_number"] for round_info in rounds]

    for table in range(1, 7):
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


def build_table_signs(experts: list[Expert]) -> list[dict[str, object]]:
    experts_by_table = build_experts_by_table(experts)
    signs: list[dict[str, object]] = []
    for table in range(1, 7):
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


def validate_schedule_integrity(trainees: list[Trainee], rounds: list[dict[str, object]]) -> None:
    all_codes = sorted(trainee.code for trainee in trainees)

    for trainee in trainees:
        route = build_route(trainee)
        if sorted(route) != [1, 2, 3, 4, 5, 6]:
            raise ValueError(
                f"{trainee.code}의 라운드 이동표가 잘못되었습니다. 현재 경로: {route}"
            )

    for round_info in rounds:
        round_number = int(round_info["round_number"])
        round_codes: list[str] = []
        for table_info in round_info["tables"]:
            table_number = int(table_info["table_number"])
            trainees_at_table = table_info["trainees"]
            if len(trainees_at_table) != 4:
                raise ValueError(
                    f"라운드 {round_number}, 테이블 {table_number}에는 연수생이 정확히 4명이어야 합니다. "
                    f"현재 {len(trainees_at_table)}명입니다."
                )
            round_codes.extend(item["code"] for item in trainees_at_table)

        if sorted(round_codes) != all_codes:
            raise ValueError(
                f"라운드 {round_number}의 전체 배치가 잘못되었습니다. 연수생 누락 또는 중복이 있습니다."
            )


def build_experts_by_table(experts: list[Expert]) -> dict[int, list[Expert]]:
    experts_by_table: dict[int, list[Expert]] = defaultdict(list)
    for expert in experts:
        experts_by_table[expert.table].append(expert)

    normalized: dict[int, list[Expert]] = {}
    for table in range(1, 7):
        normalized[table] = sorted(
            experts_by_table[table],
            key=lambda item: (item.pair_order, item.name),
        )
    return normalized


def wrap_table(value: int) -> int:
    return ((value - 1) % 6) + 1

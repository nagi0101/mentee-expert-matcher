from __future__ import annotations

import colorsys
from dataclasses import dataclass


@dataclass(frozen=True)
class ScheduleConfig:
    num_tables: int           # N
    trainees_per_table: int   # K
    experts_per_table: int    # E
    num_trainees: int         # T (actual, before phantom padding)
    num_rounds: int           # R = N
    num_groups: int           # G = K
    group_size: int           # S = N
    num_phantoms: int         # N*K - T
    group_labels: tuple[str, ...]
    group_themes: dict[str, dict[str, str]]


def build_config(
    num_trainees: int,
    num_tables: int,
    trainees_per_table: int,
    experts_per_table: int,
) -> ScheduleConfig:
    N = num_tables
    K = trainees_per_table
    T = num_trainees
    total_slots = N * K

    if T > total_slots:
        raise ValueError(
            f"연수생 {T}명이 총 슬롯 {total_slots}명(테이블 {N} × {K}명)을 초과합니다. "
            f"--trainees-per-table을 {-(-T // N)}로 올리거나 연수생 수를 줄이세요."
        )

    if T < 1:
        raise ValueError("연수생이 1명 이상이어야 합니다.")

    if N < 2:
        raise ValueError("테이블이 2개 이상이어야 합니다.")

    if K < 2:
        raise ValueError("테이블당 연수생이 2명 이상이어야 합니다.")

    num_phantoms = total_slots - T
    num_rounds = N
    num_groups = K
    group_size = N

    labels = _generate_group_labels(num_groups)
    themes = generate_group_themes(labels)

    return ScheduleConfig(
        num_tables=N,
        trainees_per_table=K,
        experts_per_table=experts_per_table,
        num_trainees=T,
        num_rounds=num_rounds,
        num_groups=num_groups,
        group_size=group_size,
        num_phantoms=num_phantoms,
        group_labels=tuple(labels),
        group_themes=themes,
    )


def _generate_group_labels(count: int) -> list[str]:
    labels = []
    for i in range(count):
        if i < 26:
            labels.append(chr(ord("A") + i))
        else:
            labels.append(f"A{chr(ord('A') + i - 26)}")
    return labels


def generate_group_themes(labels: list[str] | tuple[str, ...]) -> dict[str, dict[str, str]]:
    n = len(labels)
    themes: dict[str, dict[str, str]] = {}
    for i, label in enumerate(labels):
        hue = i / n
        accent = _hsl_to_hex(hue, 0.70, 0.45)
        soft = _hsl_to_hex(hue, 0.60, 0.93)
        ink = _hsl_to_hex(hue, 0.65, 0.30)
        themes[label] = {"accent": accent, "soft": soft, "ink": ink}
    return themes


def _hsl_to_hex(hue: float, saturation: float, lightness: float) -> str:
    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    return "#{:02x}{:02x}{:02x}".format(
        int(round(r * 255)),
        int(round(g * 255)),
        int(round(b * 255)),
    )

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.config import ScheduleConfig


CSV_CANDIDATE_ENCODINGS = ("utf-8-sig", "utf-8", "cp949", "euc-kr")


@dataclass(frozen=True)
class Trainee:
    name: str
    org: str
    group: str
    number: int
    is_phantom: bool = False

    @property
    def code(self) -> str:
        return f"{self.group}{self.number}"


@dataclass(frozen=True)
class Expert:
    name: str
    org: str
    table: int
    pair_order: int

    @property
    def is_placeholder(self) -> bool:
        return not self.name


def load_trainees(csv_path: Path) -> list[Trainee]:
    rows = _read_rows(csv_path, ("name", "org"))
    trainees: list[Trainee] = []
    for line_no, row in rows:
        name = _optional_text(row, "name")
        if not name:
            continue
        trainees.append(
            Trainee(
                name=name,
                org=_optional_text(row, "org"),
                group="",
                number=0,
            )
        )
    if not trainees:
        raise ValueError(f"{csv_path.name}: 연수생이 0명입니다.")
    return trainees


def load_experts(csv_path: Path, config: ScheduleConfig) -> list[Expert]:
    rows = _read_rows(csv_path, ("name", "org", "table"))
    experts: list[Expert] = []
    pair_counters: dict[int, int] = defaultdict(int)

    for line_no, row in rows:
        table = _parse_int(row, "table", csv_path.name, line_no)
        pair_counters[table] += 1
        experts.append(
            Expert(
                name=_optional_text(row, "name"),
                org=_optional_text(row, "org"),
                table=table,
                pair_order=pair_counters[table],
            )
        )

    validate_experts(experts, config)
    return sorted(experts, key=lambda item: (item.table, item.pair_order, item.name))


def validate_experts(experts: list[Expert], config: ScheduleConfig) -> None:
    valid_tables = set(range(1, config.num_tables + 1))

    invalid_tables = sorted({e.table for e in experts if e.table not in valid_tables})
    if invalid_tables:
        raise ValueError(
            f"table 값은 1~{config.num_tables}만 허용됩니다. "
            f"잘못된 값: {', '.join(str(v) for v in invalid_tables)}"
        )

    table_counts = Counter(e.table for e in experts)
    for table in sorted(valid_tables):
        if table_counts[table] > config.experts_per_table:
            raise ValueError(
                f"테이블 {table}에는 엑스퍼트가 최대 {config.experts_per_table}명까지 "
                f"배정될 수 있습니다. 현재 {table_counts[table]}명입니다."
            )


def assign_groups(trainees: list[Trainee], config: ScheduleConfig) -> list[Trainee]:
    """Assign group labels and numbers to trainees, adding phantoms as needed."""
    assigned: list[Trainee] = []
    idx = 0

    for g, label in enumerate(config.group_labels):
        for s in range(1, config.group_size + 1):
            if idx < len(trainees):
                t = trainees[idx]
                assigned.append(Trainee(
                    name=t.name,
                    org=t.org,
                    group=label,
                    number=s,
                    is_phantom=False,
                ))
                idx += 1
            else:
                assigned.append(Trainee(
                    name="",
                    org="",
                    group=label,
                    number=s,
                    is_phantom=True,
                ))

    return assigned


# --- CSV reading utilities (unchanged logic) ---

def _read_rows(csv_path: Path, required_headers: tuple[str, ...]) -> list[tuple[int, dict[str, str]]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

    decode_errors: list[str] = []
    header_errors: list[str] = []

    for encoding in CSV_CANDIDATE_ENCODINGS:
        try:
            with csv_path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                headers = [_normalize_header(value) for value in (reader.fieldnames or [])]
                missing = [header for header in required_headers if header not in headers]
                if missing:
                    header_errors.append(
                        f"{encoding}: 필수 열 누락 ({', '.join(missing)}) / 현재 헤더: {', '.join(headers) or '없음'}"
                    )
                    continue

                normalized_rows: list[tuple[int, dict[str, str]]] = []
                for line_no, row in enumerate(reader, start=2):
                    normalized_rows.append(
                        (
                            line_no,
                            {_normalize_header(key): value for key, value in row.items() if key is not None},
                        )
                    )
                return normalized_rows
        except UnicodeDecodeError as exc:
            decode_errors.append(f"{encoding}: {exc}")

    if header_errors:
        raise ValueError(
            f"{csv_path.name} 파일에 필수 열이 없습니다. "
            f"지원 인코딩({', '.join(CSV_CANDIDATE_ENCODINGS)})으로 읽었지만 헤더가 맞지 않습니다. "
            + " / ".join(header_errors)
        )

    raise UnicodeError(
        f"{csv_path.name} 파일 인코딩을 읽지 못했습니다. "
        f"지원 인코딩: {', '.join(CSV_CANDIDATE_ENCODINGS)}. "
        f"상세: {' / '.join(decode_errors) if decode_errors else '디코딩 시도 실패'}"
    )


def _optional_text(row: dict[str, str], field: str) -> str:
    return (row.get(field) or "").strip()


def _require_text(row: dict[str, str], field: str, file_name: str, line_no: int) -> str:
    value = _optional_text(row, field)
    if not value:
        raise ValueError(f"{file_name}:{line_no} - '{field}' 값이 비어 있습니다.")
    return value


def _parse_int(row: dict[str, str], field: str, file_name: str, line_no: int) -> int:
    raw = _require_text(row, field, file_name, line_no)
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{file_name}:{line_no} - '{field}' 값은 정수여야 합니다: {raw}") from exc


def _normalize_header(value: str | None) -> str:
    return (value or "").strip().lstrip("\ufeff")

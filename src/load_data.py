from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


VALID_GROUPS = ("A", "B", "C", "D")
VALID_TABLES = set(range(1, 7))
CSV_CANDIDATE_ENCODINGS = ("utf-8-sig", "utf-8", "cp949", "euc-kr")


@dataclass(frozen=True)
class Trainee:
    name: str
    org: str
    group: str
    number: int

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
    rows = _read_rows(csv_path, ("name", "org", "group", "number"))
    trainees: list[Trainee] = []
    for line_no, row in rows:
        trainees.append(
            Trainee(
                name=_require_text(row, "name", csv_path.name, line_no),
                org=_optional_text(row, "org"),
                group=_require_text(row, "group", csv_path.name, line_no).upper(),
                number=_parse_int(row, "number", csv_path.name, line_no),
            )
        )

    validate_trainees(trainees)
    return sorted(trainees, key=lambda item: (item.group, item.number, item.name))


def load_experts(csv_path: Path) -> list[Expert]:
    rows = _read_rows(csv_path, ("name", "org", "table", "pair_order"))
    experts: list[Expert] = []
    for line_no, row in rows:
        experts.append(
            Expert(
                name=_optional_text(row, "name"),
                org=_optional_text(row, "org"),
                table=_parse_int(row, "table", csv_path.name, line_no),
                pair_order=_parse_int(row, "pair_order", csv_path.name, line_no),
            )
        )

    validate_experts(experts)
    return sorted(experts, key=lambda item: (item.table, item.pair_order, item.name))


def validate_trainees(trainees: list[Trainee]) -> None:
    if len(trainees) != 24:
        raise ValueError(f"연수생 수는 정확히 24명이어야 합니다. 현재 {len(trainees)}명입니다.")

    invalid_groups = sorted({item.group for item in trainees if item.group not in VALID_GROUPS})
    if invalid_groups:
        raise ValueError(
            "group 값은 A/B/C/D만 허용됩니다. 잘못된 값: " + ", ".join(invalid_groups)
        )

    group_counts = Counter(item.group for item in trainees)
    for group in VALID_GROUPS:
        if group_counts[group] != 6:
            raise ValueError(
                f"{group} 그룹 인원은 정확히 6명이어야 합니다. 현재 {group_counts[group]}명입니다."
            )

    code_counts = Counter(item.code for item in trainees)
    duplicates = sorted(code for code, count in code_counts.items() if count > 1)
    if duplicates:
        raise ValueError("중복된 연수생 코드가 있습니다: " + ", ".join(duplicates))

    group_numbers: dict[str, set[int]] = defaultdict(set)
    for trainee in trainees:
        if trainee.number not in VALID_TABLES:
            raise ValueError(
                f"{trainee.code}의 number 값은 1~6이어야 합니다. 현재 {trainee.number}입니다."
            )
        group_numbers[trainee.group].add(trainee.number)

    expected = VALID_TABLES
    for group in VALID_GROUPS:
        if group_numbers[group] != expected:
            missing = sorted(expected - group_numbers[group])
            extras = sorted(group_numbers[group] - expected)
            detail_parts: list[str] = []
            if missing:
                detail_parts.append("누락: " + ", ".join(str(value) for value in missing))
            if extras:
                detail_parts.append("초과: " + ", ".join(str(value) for value in extras))
            detail = " / ".join(detail_parts) if detail_parts else "1~6 구성이 아닙니다."
            raise ValueError(f"{group} 그룹의 number 구성이 잘못되었습니다. {detail}")


def validate_experts(experts: list[Expert]) -> None:
    if len(experts) > 12:
        raise ValueError(f"엑스퍼트 수는 최대 12명까지 허용됩니다. 현재 {len(experts)}명입니다.")

    invalid_tables = sorted({item.table for item in experts if item.table not in VALID_TABLES})
    if invalid_tables:
        raise ValueError(
            "table 값은 1~6만 허용됩니다. 잘못된 값: "
            + ", ".join(str(value) for value in invalid_tables)
        )

    table_counts = Counter(item.table for item in experts)
    for table in sorted(VALID_TABLES):
        if table_counts[table] > 2:
            raise ValueError(
                f"테이블 {table}에는 엑스퍼트가 최대 2명까지 배정될 수 있습니다. 현재 {table_counts[table]}명입니다."
            )

    pair_orders: dict[int, list[int]] = defaultdict(list)
    for expert in experts:
        if expert.pair_order not in (1, 2):
            raise ValueError(
                f"{_expert_label(expert)} pair_order 값은 1 또는 2여야 합니다. 현재 {expert.pair_order}입니다."
            )
        pair_orders[expert.table].append(expert.pair_order)

    for table in sorted(VALID_TABLES):
        orders = sorted(pair_orders[table])
        if len(orders) != len(set(orders)):
            raise ValueError(
                f"테이블 {table}의 pair_order는 중복될 수 없습니다. 현재 {orders}입니다."
            )


def _expert_label(expert: Expert) -> str:
    if expert.name:
        return f"{expert.name}의"
    return f"테이블 {expert.table} 빈 슬롯의"


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


def _require_text(row: dict[str, str], field: str, file_name: str, line_no: int) -> str:
    value = _optional_text(row, field)
    if not value:
        raise ValueError(f"{file_name}:{line_no} - '{field}' 값이 비어 있습니다.")
    return value


def _optional_text(row: dict[str, str], field: str) -> str:
    return (row.get(field) or "").strip()


def _parse_int(row: dict[str, str], field: str, file_name: str, line_no: int) -> int:
    raw = _require_text(row, field, file_name, line_no)
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{file_name}:{line_no} - '{field}' 값은 정수여야 합니다: {raw}") from exc


def _normalize_header(value: str | None) -> str:
    return (value or "").strip().lstrip("\ufeff")

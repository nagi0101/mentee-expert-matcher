from __future__ import annotations

import colorsys
import hashlib
import re
import unicodedata
from dataclasses import dataclass, field


CHIP_PADDING_UNITS = 2.3
CHIP_GAP_UNITS = 0.9


@dataclass(frozen=True)
class SummaryLayout:
    max_lines: int
    line_units_by_size: dict[str, float]


@dataclass(frozen=True)
class FieldDefinition:
    key: str
    label: str
    aliases: tuple[str, ...]
    representative_aliases: tuple[str, ...]
    style: str


@dataclass
class FieldGroup:
    key: str
    label: str
    style: str
    raw_count: int = 0
    representative_raw_count: int = 0
    details: list[str] = field(default_factory=list)


SUMMARY_LAYOUTS = {
    "trainee": SummaryLayout(
        max_lines=3,
        line_units_by_size={
            "is-regular": 18.5,
            "is-compact": 20.5,
            "is-dense": 22.5,
        },
    ),
    "expert": SummaryLayout(
        max_lines=6,
        line_units_by_size={
            "is-regular": 18.5,
            "is-compact": 20.5,
            "is-dense": 22.5,
        },
    ),
}


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).strip()
    return re.sub(r"\s+", " ", normalized)


def chip_style(
    *,
    accent: str,
    ink: str,
    bg: str,
    border: str,
    dark_accent: str,
    dark_ink: str,
    dark_bg: str,
    dark_border: str,
) -> str:
    return (
        f"--interest-accent: {accent}; "
        f"--interest-ink: {ink}; "
        f"--interest-bg: {bg}; "
        f"--interest-border: {border}; "
        f"--interest-dark-accent: {dark_accent}; "
        f"--interest-dark-ink: {dark_ink}; "
        f"--interest-dark-bg: {dark_bg}; "
        f"--interest-dark-border: {dark_border};"
    )


FIELD_PALETTES = {
    "ai": {
        "accent": "#0ea5e9",
        "ink": "#075985",
        "bg": "#e0f2fe",
        "border": "#7dd3fc",
        "dark_accent": "#38bdf8",
        "dark_ink": "#e0f2fe",
        "dark_bg": "#082f49",
        "dark_border": "#0ea5e9",
    },
    "data": {
        "accent": "#10b981",
        "ink": "#065f46",
        "bg": "#d1fae5",
        "border": "#6ee7b7",
        "dark_accent": "#34d399",
        "dark_ink": "#d1fae5",
        "dark_bg": "#052e2b",
        "dark_border": "#10b981",
    },
    "backend": {
        "accent": "#3b82f6",
        "ink": "#1d4ed8",
        "bg": "#dbeafe",
        "border": "#93c5fd",
        "dark_accent": "#60a5fa",
        "dark_ink": "#dbeafe",
        "dark_bg": "#172554",
        "dark_border": "#3b82f6",
    },
    "frontend": {
        "accent": "#f59e0b",
        "ink": "#92400e",
        "bg": "#fef3c7",
        "border": "#fcd34d",
        "dark_accent": "#fbbf24",
        "dark_ink": "#fef3c7",
        "dark_bg": "#451a03",
        "dark_border": "#d97706",
    },
    "mobile": {
        "accent": "#8b5cf6",
        "ink": "#5b21b6",
        "bg": "#ede9fe",
        "border": "#c4b5fd",
        "dark_accent": "#a78bfa",
        "dark_ink": "#ede9fe",
        "dark_bg": "#2e1065",
        "dark_border": "#8b5cf6",
    },
    "unity": {
        "accent": "#ec4899",
        "ink": "#9d174d",
        "bg": "#fce7f3",
        "border": "#f9a8d4",
        "dark_accent": "#f472b6",
        "dark_ink": "#fce7f3",
        "dark_bg": "#500724",
        "dark_border": "#ec4899",
    },
    "infra": {
        "accent": "#14b8a6",
        "ink": "#115e59",
        "bg": "#ccfbf1",
        "border": "#5eead4",
        "dark_accent": "#2dd4bf",
        "dark_ink": "#ccfbf1",
        "dark_bg": "#042f2e",
        "dark_border": "#0f766e",
    },
    "planning": {
        "accent": "#84cc16",
        "ink": "#3f6212",
        "bg": "#ecfccb",
        "border": "#bef264",
        "dark_accent": "#a3e635",
        "dark_ink": "#ecfccb",
        "dark_bg": "#1a2e05",
        "dark_border": "#65a30d",
    },
    "design": {
        "accent": "#f43f5e",
        "ink": "#9f1239",
        "bg": "#ffe4e6",
        "border": "#fda4af",
        "dark_accent": "#fb7185",
        "dark_ink": "#ffe4e6",
        "dark_bg": "#4c0519",
        "dark_border": "#e11d48",
    },
    "startup": {
        "accent": "#f97316",
        "ink": "#9a3412",
        "bg": "#ffedd5",
        "border": "#fdba74",
        "dark_accent": "#fb923c",
        "dark_ink": "#ffedd5",
        "dark_bg": "#431407",
        "dark_border": "#ea580c",
    },
}


FIELD_DEFINITIONS = (
    FieldDefinition(
        key="ai",
        label="AI",
        aliases=("AI", "LLM", "ML", "MLOps", "RAG", "LangChain", "TensorFlow", "RL"),
        representative_aliases=("AI",),
        style=chip_style(**FIELD_PALETTES["ai"]),
    ),
    FieldDefinition(
        key="data",
        label="Data",
        aliases=("Data", "Data Engineering", "MySQL", "PostgreSQL", "MongoDB", "Statistics"),
        representative_aliases=("Data",),
        style=chip_style(**FIELD_PALETTES["data"]),
    ),
    FieldDefinition(
        key="backend",
        label="백엔드",
        aliases=("백엔드", "Java", "SpringBoot", "FastAPI", "Nest", "Express", "Node.js", "JPA"),
        representative_aliases=("백엔드",),
        style=chip_style(**FIELD_PALETTES["backend"]),
    ),
    FieldDefinition(
        key="frontend",
        label="프론트엔드",
        aliases=("프론트엔드", "React.js", "Next.js", "Svelte"),
        representative_aliases=("프론트엔드",),
        style=chip_style(**FIELD_PALETTES["frontend"]),
    ),
    FieldDefinition(
        key="mobile",
        label="모바일",
        aliases=("모바일", "Mobile", "Android", "iOS", "Flutter", "Kotlin", "App"),
        representative_aliases=("모바일", "Mobile"),
        style=chip_style(**FIELD_PALETTES["mobile"]),
    ),
    FieldDefinition(
        key="unity",
        label="Unity",
        aliases=("Unity", "Graphics", "C#"),
        representative_aliases=("Unity",),
        style=chip_style(**FIELD_PALETTES["unity"]),
    ),
    FieldDefinition(
        key="infra",
        label="인프라",
        aliases=("인프라", "Infra", "AWS", "Kubernetes", "Cloud", "Nginx", "Network", "home_server"),
        representative_aliases=("인프라", "Infra"),
        style=chip_style(**FIELD_PALETTES["infra"]),
    ),
    FieldDefinition(
        key="planning",
        label="기획",
        aliases=("기획", "PM", "PO", "프로덕트 엔지니어", "플랫폼", "Jira"),
        representative_aliases=("기획",),
        style=chip_style(**FIELD_PALETTES["planning"]),
    ),
    FieldDefinition(
        key="design",
        label="디자인",
        aliases=("디자인", "Figma"),
        representative_aliases=("디자인",),
        style=chip_style(**FIELD_PALETTES["design"]),
    ),
    FieldDefinition(
        key="startup",
        label="창업",
        aliases=("창업", "팀빌딩"),
        representative_aliases=("창업",),
        style=chip_style(**FIELD_PALETTES["startup"]),
    ),
)


FIELD_BY_KEY = {definition.key: definition for definition in FIELD_DEFINITIONS}
FIELD_ALIAS_TO_KEY = {
    normalize_text(alias): definition.key
    for definition in FIELD_DEFINITIONS
    for alias in definition.aliases
}
FIELD_REPRESENTATIVE_ALIASES = {
    definition.key: {normalize_text(alias) for alias in definition.representative_aliases}
    for definition in FIELD_DEFINITIONS
}


def summarize_org(org: str, layout_name: str) -> dict[str, object]:
    tags = split_org(org)
    if not tags:
        return {
            "org": org,
            "has_org": False,
            "interest_parts": [],
            "interest_items": [],
            "interest_hidden_count": 0,
            "interest_size_class": "is-regular",
        }

    groups = build_field_groups(tags)
    total_raw_count = sum(group.raw_count for group in groups)
    visible_items, visible_raw_count = fit_groups_to_layout(
        groups=groups,
        total_raw_count=total_raw_count,
        layout_name=layout_name,
    )

    hidden_count = max(0, total_raw_count - visible_raw_count)
    parts = [str(item["label"]) for item in visible_items]
    return {
        "org": org,
        "has_org": True,
        "interest_parts": parts,
        "interest_items": visible_items,
        "interest_hidden_count": hidden_count,
        "interest_size_class": size_class_for_parts(parts),
    }


def split_org(org: str) -> list[str]:
    if not org:
        return []
    normalized = unicodedata.normalize("NFKC", org)
    return list(dict.fromkeys(part for part in (normalize_text(chunk) for chunk in normalized.split("/")) if part))


def build_field_groups(tags: list[str]) -> list[FieldGroup]:
    groups: list[FieldGroup] = []
    grouped_by_key: dict[str, FieldGroup] = {}

    for tag in tags:
        normalized_tag = normalize_text(tag)
        field_key = FIELD_ALIAS_TO_KEY.get(normalized_tag)

        if field_key is None:
            group_key = f"custom:{normalized_tag.casefold()}"
            group = grouped_by_key.get(group_key)
            if group is None:
                group = FieldGroup(
                    key=group_key,
                    label=tag,
                    style=style_for_custom_tag(tag),
                )
                grouped_by_key[group_key] = group
                groups.append(group)
            group.raw_count += 1
            group.representative_raw_count += 1
            continue

        definition = FIELD_BY_KEY[field_key]
        group = grouped_by_key.get(definition.key)
        if group is None:
            group = FieldGroup(
                key=definition.key,
                label=definition.label,
                style=definition.style,
            )
            grouped_by_key[definition.key] = group
            groups.append(group)

        group.raw_count += 1
        if normalized_tag in FIELD_REPRESENTATIVE_ALIASES[definition.key]:
            group.representative_raw_count += 1
            continue

        group.details.append(tag)

    return groups


def fit_groups_to_layout(
    *,
    groups: list[FieldGroup],
    total_raw_count: int,
    layout_name: str,
) -> tuple[list[dict[str, object]], int]:
    if layout_name not in SUMMARY_LAYOUTS:
        raise ValueError(f"알 수 없는 관심사 레이아웃입니다: {layout_name}")

    visible_items: list[dict[str, object]] = []
    visible_raw_count = 0

    for group in groups:
        representative = build_interest_item(
            label=group.label,
            group_key=group.key,
            style=group.style,
            is_representative=True,
            group_start=True,
        )
        candidate_items = visible_items + [representative]
        candidate_raw_count = visible_raw_count + group.representative_raw_count
        if not fits_layout(
            items=candidate_items,
            hidden_count=max(0, total_raw_count - candidate_raw_count),
            layout_name=layout_name,
        ):
            break

        visible_items = candidate_items
        visible_raw_count = candidate_raw_count

        for detail in group.details:
            detail_item = build_interest_item(
                label=detail,
                group_key=group.key,
                style=group.style,
                is_representative=False,
                group_start=False,
            )
            candidate_items = visible_items + [detail_item]
            candidate_raw_count = visible_raw_count + 1
            if not fits_layout(
                items=candidate_items,
                hidden_count=max(0, total_raw_count - candidate_raw_count),
                layout_name=layout_name,
            ):
                break

            visible_items = candidate_items
            visible_raw_count = candidate_raw_count

    if visible_items:
        return visible_items, visible_raw_count

    first_group = groups[0]
    return (
        [
            build_interest_item(
                label=first_group.label,
                group_key=first_group.key,
                style=first_group.style,
                is_representative=True,
                group_start=True,
            )
        ],
        first_group.representative_raw_count,
    )


def build_interest_item(
    *,
    label: str,
    group_key: str,
    style: str,
    is_representative: bool,
    group_start: bool,
) -> dict[str, object]:
    return {
        "label": label,
        "group_key": group_key,
        "style": style,
        "is_representative": is_representative,
        "group_start": group_start,
    }


def fits_layout(
    *,
    items: list[dict[str, object]],
    hidden_count: int,
    layout_name: str,
) -> bool:
    parts = [str(item["label"]) for item in items]
    size_class = size_class_for_parts(parts)
    layout = SUMMARY_LAYOUTS[layout_name]
    available_units = layout.max_lines * layout.line_units_by_size[size_class]
    required_units = summary_width_units(parts, hidden_count)
    return required_units <= available_units


def size_class_for_parts(parts: list[str]) -> str:
    width_units = summary_width_units(parts, hidden_count=0)
    if len(parts) >= 7 or width_units >= 42:
        return "is-dense"
    if len(parts) >= 5 or width_units >= 26:
        return "is-compact"
    return "is-regular"


def summary_width_units(parts: list[str], hidden_count: int) -> float:
    if not parts:
        return 0.0

    width = sum(chip_width_units(part) for part in parts)
    width += max(0, len(parts) - 1) * CHIP_GAP_UNITS
    if hidden_count > 0:
        width += CHIP_GAP_UNITS + chip_width_units(f"+{hidden_count}")
    return width


def display_width_units(text: str) -> float:
    width = 0.0
    for char in normalize_text(text):
        if char.isspace():
            width += 0.32
            continue

        east_asian = unicodedata.east_asian_width(char)
        if east_asian in {"W", "F"}:
            width += 1.0
            continue

        if char.isalpha() or char.isdigit():
            width += 0.62
            continue

        width += 0.42
    return width


def chip_width_units(text: str) -> float:
    return display_width_units(text) + CHIP_PADDING_UNITS


def style_for_custom_tag(tag: str) -> str:
    normalized = normalize_text(tag).casefold()
    digest = hashlib.blake2s(normalized.encode("utf-8"), digest_size=2).digest()
    hue = int.from_bytes(digest, byteorder="big") % 360
    hue_ratio = hue / 360
    return chip_style(
        accent=hsl_to_hex(hue_ratio, 0.72, 0.48),
        ink=hsl_to_hex(hue_ratio, 0.62, 0.26),
        bg=hsl_to_hex(hue_ratio, 0.60, 0.93),
        border=hsl_to_hex(hue_ratio, 0.62, 0.78),
        dark_accent=hsl_to_hex(hue_ratio, 0.68, 0.58),
        dark_ink=hsl_to_hex(hue_ratio, 0.48, 0.94),
        dark_bg=hsl_to_hex(hue_ratio, 0.42, 0.18),
        dark_border=hsl_to_hex(hue_ratio, 0.52, 0.38),
    )


def hsl_to_hex(hue: float, saturation: float, lightness: float) -> str:
    red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)
    return "#{:02x}{:02x}{:02x}".format(
        int(round(red * 255)),
        int(round(green * 255)),
        int(round(blue * 255)),
    )


def default_chip_style() -> str:
    return chip_style(
        accent="#94a3b8",
        ink="#334155",
        bg="#f8fafc",
        border="#cbd5e1",
        dark_accent="#94a3b8",
        dark_ink="#f8fafc",
        dark_bg="#1e293b",
        dark_border="#64748b",
    )

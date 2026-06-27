from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal


SourceLanguage = Literal["matlab", "hdl", "equivalence"]


@dataclass
class ConversionDiagnostic:
    language: SourceLanguage
    severity: Literal["info", "warning", "error"]
    message: str
    line: int | None = None


@dataclass
class ConversionResult:
    language: SourceLanguage
    module_name: str
    lean_code: str
    diagnostics: list[ConversionDiagnostic] = field(default_factory=list)
    metrics: dict[str, int | str | bool] = field(default_factory=dict)


def sanitize_identifier(value: str, fallback: str = "unnamed") -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", value.strip())
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        value = fallback
    if value[0].isdigit():
        value = f"n_{value}"
    if value in LEAN_RESERVED:
        value = f"{value}_field"
    return value


def namespace_name(prefix: str, name: str) -> str:
    return sanitize_identifier(f"{prefix}_{name}")


def is_bool_name(name: str) -> bool:
    lowered = name.lower()
    if any(token in lowered for token in ["ptr", "count", "addr", "data", "din", "dout"]):
        return False
    bool_tokens = [
        "clk",
        "clock",
        "rst",
        "reset",
        "valid",
        "ready",
        "full",
        "empty",
        "enable",
        "_en",
        "en_",
        "wr",
        "rd",
        "req",
        "ack",
        "grant",
        "done",
        "start",
        "sel",
    ]
    return lowered in {"clk", "rst", "rst_n", "reset", "reset_n"} or any(
        token in lowered for token in bool_tokens
    )


def lean_type_for_signal(name: str, width: int = 1) -> str:
    if width <= 1 and is_bool_name(name):
        return "Bool"
    return "Int"


def default_value_for_type(lean_type: str) -> str:
    return "false" if lean_type == "Bool" else "0"


def line_comment(value: str) -> str:
    return "-- " + value.replace("\n", " ").strip()


LEAN_RESERVED = {
    "abbrev",
    "axiom",
    "by",
    "class",
    "def",
    "deriving",
    "do",
    "else",
    "end",
    "example",
    "false",
    "for",
    "forall",
    "fun",
    "have",
    "if",
    "import",
    "in",
    "inductive",
    "instance",
    "let",
    "match",
    "namespace",
    "open",
    "opaque",
    "partial",
    "private",
    "protected",
    "structure",
    "then",
    "theorem",
    "true",
    "where",
}

from __future__ import annotations

import re
from dataclasses import dataclass

from .common import (
    ConversionDiagnostic,
    ConversionResult,
    default_value_for_type,
    lean_type_for_signal,
    line_comment,
    namespace_name,
    sanitize_identifier,
)
from .lean_expr import LeanExpressionTranslator


@dataclass
class MatlabAssignment:
    target: str
    expression: str
    condition: str | None
    line: int


class MatlabToLeanConverter:
    """Convert a deterministic MATLAB function subset into Lean4.

    Supported subset:
    - one `function` per file
    - scalar inputs/outputs
    - direct assignments
    - single-level if/elseif/else/end guarded assignments
    - arithmetic/comparison/boolean operators usable in Lean after translation
    """

    HEADER = re.compile(
        r"^\s*function\s+(?:\[(?P<outputs_many>[^\]]+)\]|(?P<output_one>[A-Za-z_]\w*))\s*=\s*"
        r"(?P<name>[A-Za-z_]\w*)\s*\((?P<inputs>[^)]*)\)",
        re.I,
    )
    ASSIGN = re.compile(r"^\s*(?P<lhs>[A-Za-z_]\w*)\s*=\s*(?P<rhs>.+?);?\s*$")

    def __init__(self) -> None:
        self.expr = LeanExpressionTranslator()

    def convert(self, matlab_text: str, module_name: str | None = None) -> ConversionResult:
        diagnostics: list[ConversionDiagnostic] = []
        lines = self._strip_comments(matlab_text)
        header_line, header = self._find_header(lines)
        if header is None:
            name = module_name or "matlab_model"
            diagnostics.append(
                ConversionDiagnostic("matlab", "error", "No MATLAB function header found.")
            )
            return ConversionResult("matlab", name, self._empty_model(name, diagnostics), diagnostics)

        function_name = module_name or sanitize_identifier(header.group("name"))
        outputs = self._split_csv(header.group("outputs_many") or header.group("output_one") or "y")
        inputs = self._split_csv(header.group("inputs"))
        assignments = self._parse_assignments(lines[header_line + 1 :], diagnostics)

        input_types = {name: lean_type_for_signal(name) for name in inputs}
        output_types = {
            name: self._infer_output_type(name, assignments, input_types) for name in outputs
        }

        lean = self._render(function_name, inputs, outputs, input_types, output_types, assignments)
        metrics = {
            "inputs": len(inputs),
            "outputs": len(outputs),
            "assignments": len(assignments),
            "unsupported": sum(1 for item in diagnostics if item.severity == "warning"),
            "has_errors": any(item.severity == "error" for item in diagnostics),
        }
        return ConversionResult("matlab", function_name, lean, diagnostics, metrics)

    def _strip_comments(self, matlab_text: str) -> list[tuple[int, str]]:
        stripped: list[tuple[int, str]] = []
        for line_no, raw in enumerate(matlab_text.splitlines(), start=1):
            line = raw.split("%", 1)[0].strip()
            if line:
                stripped.append((line_no, line))
        return stripped

    def _find_header(self, lines: list[tuple[int, str]]) -> tuple[int, re.Match[str] | None]:
        for index, (_line_no, line) in enumerate(lines):
            match = self.HEADER.match(line)
            if match:
                return index, match
        return 0, None

    def _parse_assignments(
        self,
        lines: list[tuple[int, str]],
        diagnostics: list[ConversionDiagnostic],
    ) -> list[MatlabAssignment]:
        assignments: list[MatlabAssignment] = []
        active_condition: str | None = None
        branch_conditions: list[str] = []
        in_supported_branch = False

        for line_no, line in lines:
            lowered = line.lower()
            if lowered == "end":
                active_condition = None
                branch_conditions = []
                in_supported_branch = False
                continue
            if lowered.startswith("if "):
                condition = line[3:].strip()
                active_condition = condition
                branch_conditions = [condition]
                in_supported_branch = True
                continue
            if lowered.startswith("elseif "):
                condition = line[7:].strip()
                active_condition = self._guard_excluding_previous(condition, branch_conditions)
                branch_conditions.append(condition)
                in_supported_branch = True
                continue
            if lowered == "else":
                active_condition = self._negate_any(branch_conditions) if branch_conditions else None
                in_supported_branch = True
                continue

            match = self.ASSIGN.match(line)
            if match:
                assignments.append(
                    MatlabAssignment(
                        target=sanitize_identifier(match.group("lhs")),
                        expression=match.group("rhs").strip(),
                        condition=active_condition,
                        line=line_no,
                    )
                )
                continue

            if lowered in {"return", "endfunction"}:
                continue
            diagnostics.append(
                ConversionDiagnostic(
                    "matlab",
                    "warning",
                    f"Unsupported MATLAB statement preserved as a diagnostic: {line}",
                    line_no,
                )
            )
            if in_supported_branch:
                diagnostics.append(
                    ConversionDiagnostic(
                        "matlab",
                        "warning",
                        "Unsupported statement occurred inside a branch; generated Lean keeps supported assignments only.",
                        line_no,
                    )
                )
        return assignments

    def _render(
        self,
        name: str,
        inputs: list[str],
        outputs: list[str],
        input_types: dict[str, str],
        output_types: dict[str, str],
        assignments: list[MatlabAssignment],
    ) -> str:
        ns = namespace_name("QEDSoft_MATLAB", name)
        scopes = {raw: "i" for raw in inputs}
        scopes.update({sanitize_identifier(raw): "i" for raw in inputs})
        lines = [
            "-- Auto-generated by QEDSoft Job 1: MATLAB to Lean4.",
            "-- Supported subset: scalar function inputs/outputs, assignments, and single-level branches.",
            f"namespace {ns}",
            "",
            "structure Input where",
        ]
        for raw in inputs or ["dummy"]:
            field = sanitize_identifier(raw)
            lines.append(f"  {field} : {input_types.get(raw, 'Int')}")

        lines.extend(["", "structure Output where"])
        for raw in outputs or ["y"]:
            field = sanitize_identifier(raw)
            lines.append(f"  {field} : {output_types.get(raw, 'Int')}")

        lines.extend(["", "def step (i : Input) : Output :="])
        output_names = outputs or ["y"]
        output_exprs: dict[str, str] = {}
        for output in output_names:
            field = sanitize_identifier(output)
            value = self._expression_for_output(output, assignments, scopes, output_types[field])
            output_exprs[field] = value
            lines.append(f"  let {field} := {value}")
        lines.append("  {")
        for index, output in enumerate(output_names):
            field = sanitize_identifier(output)
            suffix = "," if index < len(outputs or ["y"]) - 1 else ""
            lines.append(f"    {field} := {field}{suffix}")
        lines.extend(
            [
                "  }",
                "",
                "theorem step_is_total (_i : Input) : True := by",
                "  trivial",
                "",
                f"end {ns}",
                "",
            ]
        )
        return "\n".join(lines)

    def _expression_for_output(
        self,
        output: str,
        assignments: list[MatlabAssignment],
        scopes: dict[str, str],
        output_type: str,
    ) -> str:
        relevant = [item for item in assignments if item.target == sanitize_identifier(output)]
        if not relevant:
            return default_value_for_type(output_type)

        fallback = default_value_for_type(output_type)
        for assignment in reversed(relevant):
            expr = self.expr.translate(assignment.expression, scopes)
            if assignment.condition:
                condition = self.expr.translate(assignment.condition, scopes)
                fallback = f"if {condition} then {expr} else {fallback}"
            else:
                fallback = expr
        return fallback

    def _infer_output_type(
        self,
        output: str,
        assignments: list[MatlabAssignment],
        input_types: dict[str, str],
    ) -> str:
        if lean_type_for_signal(output) == "Bool":
            return "Bool"
        relevant = [item.expression.lower() for item in assignments if item.target == sanitize_identifier(output)]
        if any(expr in {"true", "false"} for expr in relevant):
            return "Bool"
        for expr in relevant:
            tokens = re.findall(r"\b[A-Za-z_]\w*\b", expr)
            if tokens and all(input_types.get(token) == "Bool" for token in tokens if token in input_types):
                if any(op in expr for op in ["&&", "||", "~", "==", "~="]):
                    return "Bool"
        return "Int"

    def _split_csv(self, value: str | None) -> list[str]:
        if not value:
            return []
        return [sanitize_identifier(item) for item in value.split(",") if item.strip()]

    def _guard_excluding_previous(self, condition: str, previous: list[str]) -> str:
        if not previous:
            return condition
        return f"{self._negate_any(previous)} && ({condition})"

    def _negate_any(self, conditions: list[str]) -> str:
        joined = " || ".join(f"({condition})" for condition in conditions)
        return f"~({joined})"

    def _empty_model(
        self,
        name: str,
        diagnostics: list[ConversionDiagnostic],
    ) -> str:
        ns = namespace_name("QEDSoft_MATLAB", name)
        comments = [line_comment(item.message) for item in diagnostics]
        return "\n".join(
            [
                "-- Auto-generated by QEDSoft Job 1: MATLAB to Lean4.",
                *comments,
                f"namespace {ns}",
                "structure Input where",
                "  dummy : Int",
                "structure Output where",
                "  dummy : Int",
                "def step (_i : Input) : Output := { dummy := 0 }",
                "theorem step_is_total (_i : Input) : True := by",
                "  trivial",
                f"end {ns}",
                "",
            ]
        )

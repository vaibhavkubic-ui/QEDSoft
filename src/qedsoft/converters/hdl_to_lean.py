from __future__ import annotations

import re
from dataclasses import dataclass

from .common import (
    ConversionDiagnostic,
    ConversionResult,
    default_value_for_type,
    lean_type_for_signal,
    namespace_name,
    sanitize_identifier,
)
from .lean_expr import LeanExpressionTranslator


@dataclass
class HDLSignal:
    name: str
    direction: str
    lean_type: str
    width: int = 1


@dataclass
class HDLAssign:
    target: str
    expression: str


class HDLToLeanConverter:
    """Convert a synthesizable RTL subset into a Lean4 transition skeleton.

    Supported subset:
    - one Verilog/SystemVerilog module
    - ANSI-style scalar/vector ports
    - integer parameters with literal defaults
    - continuous assignments
    - reset assignments inside always blocks, used to seed reset_state
    """

    MODULE = re.compile(r"\bmodule\s+([A-Za-z_]\w*)\s*(?P<rest>.*?)\s*;", re.S)
    PARAM = re.compile(r"\bparameter\s+(?:int\s+)?([A-Za-z_]\w*)\s*=\s*([0-9]+)")
    PORT = re.compile(
        r"\b(input|output|inout)\b\s+(?:wire|logic|reg|signed|unsigned|\s)*"
        r"(?P<width>\[[^\]]+\])?\s*(?P<name>[A-Za-z_]\w*)",
        re.I,
    )
    INTERNAL = re.compile(r"^\s*logic\s+(?P<width>\[[^\]]+\])?\s*(?P<name>[A-Za-z_]\w*)\s*;", re.M)
    ASSIGN = re.compile(r"\bassign\s+([A-Za-z_]\w*)\s*=\s*(.+?)\s*;", re.S)
    NONBLOCKING = re.compile(r"\b([A-Za-z_]\w*)\s*<=\s*(.+?)\s*;")

    def __init__(self) -> None:
        self.expr = LeanExpressionTranslator()

    def convert(self, hdl_text: str, module_name: str | None = None) -> ConversionResult:
        diagnostics: list[ConversionDiagnostic] = []
        module_match = self.MODULE.search(hdl_text)
        inferred_name = module_name or (module_match.group(1) if module_match else "hdl_model")
        module = sanitize_identifier(inferred_name)

        parameters = self._parse_parameters(hdl_text)
        ports = self._parse_ports(hdl_text, diagnostics)
        internals = self._parse_internal_state(hdl_text, ports)
        assigns = self._parse_assigns(hdl_text)
        sequential_targets = self._parse_sequential_targets(hdl_text)
        reset_values = self._parse_reset_values(hdl_text)

        state_names = sorted(set(internals) | sequential_targets | {p.name for p in ports if p.direction == "output"})
        lean = self._render(module, parameters, ports, state_names, assigns, reset_values)
        metrics = {
            "ports": len(ports),
            "state_fields": len(state_names),
            "continuous_assigns": len(assigns),
            "reset_values": len(reset_values),
            "has_errors": any(item.severity == "error" for item in diagnostics),
        }
        return ConversionResult("hdl", module, lean, diagnostics, metrics)

    def _parse_parameters(self, hdl_text: str) -> dict[str, str]:
        return {
            sanitize_identifier(name): value
            for name, value in self.PARAM.findall(hdl_text)
        }

    def _parse_ports(
        self,
        hdl_text: str,
        diagnostics: list[ConversionDiagnostic],
    ) -> list[HDLSignal]:
        ports: list[HDLSignal] = []
        module_match = self.MODULE.search(hdl_text)
        search_area = module_match.group("rest") if module_match else hdl_text
        search_area = search_area.replace("\n", " ")
        for segment in search_area.split(","):
            match = self.PORT.search(segment)
            if not match:
                continue
            name = sanitize_identifier(match.group("name"))
            width = self._width_from_range(match.group("width") or "")
            ports.append(
                HDLSignal(
                    name=name,
                    direction=match.group(1).lower(),
                    width=width,
                    lean_type=lean_type_for_signal(name, width),
                )
            )
        if not ports:
            diagnostics.append(
                ConversionDiagnostic("hdl", "warning", "No ANSI-style HDL ports were extracted.")
            )
        return self._dedupe_ports(ports)

    def _parse_internal_state(self, hdl_text: str, ports: list[HDLSignal]) -> set[str]:
        port_names = {port.name for port in ports}
        internals: set[str] = set()
        for match in self.INTERNAL.finditer(hdl_text):
            name = sanitize_identifier(match.group("name"))
            if name not in port_names:
                internals.add(name)
        return internals

    def _parse_assigns(self, hdl_text: str) -> list[HDLAssign]:
        return [
            HDLAssign(sanitize_identifier(target), expression.strip())
            for target, expression in self.ASSIGN.findall(hdl_text)
        ]

    def _parse_sequential_targets(self, hdl_text: str) -> set[str]:
        return {sanitize_identifier(target) for target, _expr in self.NONBLOCKING.findall(hdl_text)}

    def _parse_reset_values(self, hdl_text: str) -> dict[str, str]:
        values: dict[str, str] = {}
        reset_block = re.search(r"if\s*\([^)]*rst[^)]*\)\s*begin(?P<body>.*?)end", hdl_text, re.S | re.I)
        if not reset_block:
            reset_block = re.search(r"if\s*\([^)]*reset[^)]*\)\s*begin(?P<body>.*?)end", hdl_text, re.S | re.I)
        if not reset_block:
            return values
        for target, expr in self.NONBLOCKING.findall(reset_block.group("body")):
            values[sanitize_identifier(target)] = expr.strip()
        return values

    def _render(
        self,
        module: str,
        parameters: dict[str, str],
        ports: list[HDLSignal],
        state_names: list[str],
        assigns: list[HDLAssign],
        reset_values: dict[str, str],
    ) -> str:
        ns = namespace_name("QEDSoft_HDL", module)
        input_ports = [port for port in ports if port.direction == "input"]
        output_ports = [port for port in ports if port.direction == "output"]
        state_types = {
            name: self._type_for_name(name, ports)
            for name in state_names
        }
        scopes = {port.name: "i" for port in input_ports}
        scopes.update({name: "s" for name in state_names})
        constants = set(parameters)

        lines = [
            "-- Auto-generated by QEDSoft Job 1: HDL to Lean4.",
            "-- This is a structural transition skeleton for formal refinement work.",
            f"namespace {ns}",
            "",
        ]
        for name, value in parameters.items():
            lines.append(f"def {name} : Int := {value}")
        if parameters:
            lines.append("")

        lines.append("structure Input where")
        for port in input_ports or [HDLSignal("dummy", "input", "Int")]:
            lines.append(f"  {port.name} : {port.lean_type}")

        lines.extend(["", "structure State where"])
        for name in state_names or ["dummy"]:
            lines.append(f"  {name} : {state_types.get(name, 'Int')}")

        lines.extend(["", "structure Output where"])
        for port in output_ports or [HDLSignal("dummy", "output", "Int")]:
            lines.append(f"  {port.name} : {port.lean_type}")

        lines.extend(["", "def reset_state : State :=", "  {"])
        for index, name in enumerate(state_names or ["dummy"]):
            raw_value = reset_values.get(name, default_value_for_type(state_types.get(name, "Int")))
            value = self.expr.translate(raw_value, scopes, constants)
            suffix = "," if index < len(state_names or ["dummy"]) - 1 else ""
            lines.append(f"    {name} := {value}{suffix}")
        lines.extend(["  }", ""])

        lines.extend(["def output (_i : Input) (s : State) : Output :=", "  {"])
        assign_by_target = {assign.target: assign.expression for assign in assigns}
        for index, port in enumerate(output_ports or [HDLSignal("dummy", "output", "Int")]):
            if port.name in assign_by_target:
                value = self.expr.translate(assign_by_target[port.name], scopes, constants)
            elif port.name in state_names:
                value = f"s.{port.name}"
            else:
                value = default_value_for_type(port.lean_type)
            suffix = "," if index < len(output_ports or [port]) - 1 else ""
            lines.append(f"    {port.name} := {value}{suffix}")
        lines.extend(["  }", ""])

        lines.extend(
            [
                "-- Sequential always-block semantics are conservatively represented as a total step.",
                "-- Extend this function with parsed nonblocking-assignment semantics for signoff-grade proofs.",
                "def step (_i : Input) (s : State) : State := s",
                "",
                "theorem step_is_total (_i : Input) (_s : State) : True := by",
                "  trivial",
                "",
                f"end {ns}",
                "",
            ]
        )
        return "\n".join(lines)

    def _type_for_name(self, name: str, ports: list[HDLSignal]) -> str:
        for port in ports:
            if port.name == name:
                return port.lean_type
        return lean_type_for_signal(name)

    def _width_from_range(self, width_range: str) -> int:
        if not width_range or re.search(r"[A-Za-z_]", width_range):
            return 1
        numbers = [int(item) for item in re.findall(r"\d+", width_range)]
        if len(numbers) >= 2:
            return abs(numbers[0] - numbers[1]) + 1
        return 1

    def _dedupe_ports(self, ports: list[HDLSignal]) -> list[HDLSignal]:
        deduped: dict[str, HDLSignal] = {}
        for port in ports:
            deduped[port.name] = port
        return list(deduped.values())

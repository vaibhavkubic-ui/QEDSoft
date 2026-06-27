from __future__ import annotations

import argparse
from pathlib import Path

from qedsoft.converters import HDLToLeanConverter, MatlabToLeanConverter
from qedsoft.models import ProjectConfig
from qedsoft.orchestrator import QEDSoft


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qedsoft",
        description="QEDSoft: natural-language to formal RTL verification artifacts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify", help="Generate and verify SVA/Lean artifacts.")
    verify.add_argument("--spec", required=True, type=Path, help="Natural-language chip spec.")
    verify.add_argument("--rtl", type=Path, help="Optional RTL/SystemVerilog source.")
    verify.add_argument("--matlab", type=Path, help="Optional MATLAB golden model source.")
    verify.add_argument("--out", type=Path, default=Path("runs/qedsoft"), help="Output directory.")
    verify.add_argument("--top", help="Override top module name.")
    verify.add_argument("--clock", help="Override clock signal.")
    verify.add_argument("--reset", help="Override reset signal.")
    verify.add_argument("--reset-active-high", action="store_true", help="Treat reset as active high.")
    verify.add_argument("--no-external-tools", action="store_true", help="Skip Lean/EDA tool subprocesses.")
    verify.add_argument("--repair-rounds", type=int, default=2, help="Max structured repair rounds.")
    verify.add_argument("--memory", type=Path, help="Optional feedback-memory JSON path.")
    verify.add_argument("--no-source-to-lean", action="store_true", help="Disable MATLAB/HDL to Lean4 Job 1.")

    convert = subparsers.add_parser("convert", help="Run Job 1 only: convert MATLAB or HDL to Lean4.")
    convert.add_argument("--matlab", type=Path, help="MATLAB source to convert.")
    convert.add_argument("--hdl", type=Path, help="HDL/SystemVerilog source to convert.")
    convert.add_argument("--out", type=Path, default=Path("runs/convert"), help="Output directory.")
    convert.add_argument("--name", help="Override generated Lean module name.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "verify":
        config = ProjectConfig(
            top_module=args.top,
            clock=args.clock,
            reset=args.reset,
            reset_active_low=False if args.reset_active_high else None,
            use_external_tools=not args.no_external_tools,
            max_repair_rounds=args.repair_rounds,
            memory_path=args.memory,
            enable_source_to_lean=not args.no_source_to_lean,
        )
        result = QEDSoft(config).run_from_paths(args.spec, args.rtl, args.matlab, args.out)
        print(f"QEDSoft output: {result.output_dir}")
        print(f"Success: {result.success}")
        print(f"Report: {result.output_dir / 'qedsoft_report.md'}")
        return 0 if result.success else 2

    if args.command == "convert":
        args.out.mkdir(parents=True, exist_ok=True)
        wrote_any = False
        if args.matlab:
            source = args.matlab.read_text(encoding="utf-8")
            result = MatlabToLeanConverter().convert(source, module_name=args.name or args.matlab.stem)
            path = args.out / f"{result.module_name}_matlab_model.lean"
            path.write_text(result.lean_code, encoding="utf-8")
            print(f"MATLAB Lean4 model: {path}")
            for diagnostic in result.diagnostics:
                print(f"{diagnostic.severity.upper()}: {diagnostic.message}")
            wrote_any = True
        if args.hdl:
            source = args.hdl.read_text(encoding="utf-8")
            result = HDLToLeanConverter().convert(source, module_name=args.name or args.hdl.stem)
            path = args.out / f"{result.module_name}_hdl_model.lean"
            path.write_text(result.lean_code, encoding="utf-8")
            print(f"HDL Lean4 model: {path}")
            for diagnostic in result.diagnostics:
                print(f"{diagnostic.severity.upper()}: {diagnostic.message}")
            wrote_any = True
        if not wrote_any:
            parser.error("convert requires --matlab and/or --hdl")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
